import json
import logging
import urllib
from datetime import datetime
from urllib import quote
from distutils.version import LooseVersion
from django.conf import settings
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from mpinstaller.auth import SalesforceOAuth2
from mpinstaller.installer import version_install_map
from mpinstaller.installer import install_map_to_package_list
from mpinstaller.installer import install_map_to_json
from mpinstaller.mdapi import ApiListMetadata
from mpinstaller.mdapi import ApiRetrieveInstalledPackages
from mpinstaller.models import InstallationError
from mpinstaller.models import Package
from mpinstaller.models import PackageInstallation
from mpinstaller.models import PackageInstallationSession
from mpinstaller.models import PackageInstallationStep
from mpinstaller.models import PackageVersion
from mpinstaller.package import PackageZipBuilder
from mpinstaller.utils import obscure_salesforce_log
from simple_salesforce import Salesforce
from simple_salesforce.api import SalesforceExpiredSession
from simple_salesforce.api import SalesforceResourceNotFound

logger = logging.getLogger(__name__)

def package_overview(request, namespace, beta=None, github=None):
    package = get_object_or_404(Package, namespace = namespace)

    if beta:
        suffix = 'beta'
    elif github:
        suffix = 'github'
    else:
        suffix = 'prod'

    current_version = getattr(package, 'current_%s' % suffix)
    if current_version:
        return package_version_overview(request, namespace, current_version.id)

    return render_to_response('mpinstaller/package_overview_no_version.html', {'package': package, 'beta': beta, 'github': github})

def package_version_overview(request, namespace, version_id):
    version = get_object_or_404(PackageVersion, package__namespace = namespace, id=version_id)

    fork = request.GET.get('fork',None)
    git_ref = request.GET.get('git_ref',None)

    oauth = request.session.get('oauth')

    request.session['mpinstaller_current_version'] = version.id

    install_map = []
    package_list = []
    if oauth and oauth.get('access_token', None):
        org_packages = request.session.get('org_packages', None)
        metadata = request.session.get('metadata', None)
        if org_packages is None or metadata is None:
            if 'post_login_redirected' not in request.session:
                request.session['mpinstaller_redirect'] = request.build_absolute_uri(request.path)
                request.session['post_login_redirected'] = False
                return HttpResponseRedirect(request.build_absolute_uri('/mpinstaller/oauth/post_login'))
            else:
                del request.session['post_login_redirected']
                redirect = quote(request.build_absolute_uri(request.path))
                return HttpResponseRedirect(request.build_absolute_uri('/mpinstaller/oauth/logout?redirect=%s' % redirect))
                
        elif 'post_login_redirected' in request.session:
            del request.session['post_login_redirected']

        # Ensure installation is available in connected org, logout and redirect if not
        reason = check_installation_available(request, version)
        if reason:
            return HttpResponseRedirect('/mpinstaller/%s/version/%s/installation-unavailable/%s' % (version.package.namespace, version.id, reason))

        # Get the install map and package list
        install_map = version_install_map(version, org_packages, metadata, git_ref, fork)
        package_list = install_map_to_package_list(install_map)
    
    logged_in = False
    redirect = quote(request.build_absolute_uri(request.path))
    if oauth and oauth.get('access_token', None):
        login_url = None
        logout_url = request.build_absolute_uri('/mpinstaller/oauth/logout?redirect=%s' % redirect)
    else:
        login_url = request.build_absolute_uri('/mpinstaller/oauth/login?redirect=%s' % redirect)
        logout_url = None

    install_url = request.build_absolute_uri('/mpinstaller/%s/version/%s/install' % (namespace, version_id))
    if git_ref:
        install_url += '?git_ref=%s' % urllib.quote(git_ref)
        if fork:
            install_url += '&fork=%s' % urllib.quote(fork)
    elif fork:
        install_url += '?fork=%s' % urllib.quote(fork)

    repo_url = version.repo_url
    if repo_url and fork:
        repo_url_parts = repo_url.split('/')
        repo_url_parts[3] = fork
        repo_url = '/'.join(repo_url_parts)

    data = {
        'version': version,
        'oauth': request.session.get('oauth',None),
        'git_ref': git_ref,
        'fork': fork,
        'repo_url': repo_url,
        'login_url': login_url,
        'logout_url': logout_url,
        'install_url': install_url,
        'base_url': request.build_absolute_uri('/mpinstaller/'),
        'package_list': package_list,
        'install_map': install_map,
        'content_intro': version.get_content_intro(),
    }

    return render_to_response('mpinstaller/package_version_overview.html', data)

def check_installation_available(request, version):
    """ Checks if the installation is available and returns a reason code string if install is unavailable """
    oauth = request.session.get('oauth', None)

    # If not connected, redirect to the install url
    if oauth == 'None' or 'access_token' not in oauth:
        return HttpResponseRedirect(version.get_installer_url(request))

    # If the user does not have Modify All Data permissions, don't allow install
    if not oauth.get('perm_modifyalldata'):
        return 'modify-all-data'

    # If the install requires beta versions, verify org type
    if version.requires_beta():
        if not oauth.get('sandbox',False) and oauth['org_type'].find('Developer Edition') == -1:
            return 'beta-in-prod-org'

    # Allow passing of ?bypass_sandbox=true to bypass a sandbox installation
    bypass_sandbox = request.session.get('bypass_sandbox', None)
    if bypass_sandbox == None:
        bypass_sandbox = request.GET.get('bypass_sandbox',False) == 'true'
        if bypass_sandbox:
            request.session['bypass_sandbox'] = bypass_sandbox

    # If the package requires a sandbox installation before a production upgrade,
    # verify this version has been installed in a sandbox of the org
    if not version.is_beta() and version.package.force_sandbox and bypass_sandbox:
        # Is this a production org?
        if oauth.get('org_type', None) == 'Enterprise Edition':
            # Is this an upgrade?
            is_upgrade = False
            for namespace, installed_version in request.session.get('org_packages', {}).items():
                if installed_version != None:
                    is_upgrade = True
                    break
            if is_upgrade:
                # Check if a previous successful installation exists on a sandbox of the org
                sandbox_installs = PackageInstallation.objects.filter(
                    version = version,
                    org_type__contains = '(Sandbox)',
                    username__startswith = '%s.' % oauth.get('username', ''),
                    status = 'Succeeded',
                )
                if not sandbox_installs.count():
                    return 'sandbox-required'

def installation_unavailable(request, namespace, version_id, reason):
    version = get_object_or_404(PackageVersion, package__namespace = namespace, id=version_id)

    if 'oauth' in request.session:
        redirect = quote(request.build_absolute_uri('/mpinstaller/%s/version/%s/installation-unavailable/%s' % (version.package.namespace, version.id, reason)))
        return HttpResponseRedirect(request.build_absolute_uri('/mpinstaller/oauth/logout?redirect=%s' % redirect))

    install_url = version.get_installer_url(request)

    data = {
        'version': version,
        'install_url': install_url,
        'reason': reason,
    }

    return render_to_response('mpinstaller/installation_unavailable.html', data)

def start_package_installation(request, namespace, version_id):
    """ Kicks off a package installation and redirects to the installation's page """
    version = get_object_or_404(PackageVersion, package__namespace=namespace, id=version_id)
    oauth = request.session.get('oauth', None)

    git_ref = request.GET.get('git_ref',None)
    fork = request.GET.get('fork',None)

    # Redirect back to the package overview page if not connected to an org
    if not oauth or not oauth.get('access_token'):
        redirect = version.get_installer_url(request)
        return HttpResponseRedirect(redirect)
   
    # Ensure installation is available in connected org, logout and redirect if not
    reason = check_installation_available(request, version)
    if reason:
        return HttpResponseRedirect('/mpinstaller/%s/version/%s/installation-unavailable/%s' % (version.package.namespace, version.id, reason))

    # This view should only be used for executing a map already reviewed by the user.
    # If there is no installed list or metadata list in session, that didn't happen for some reason 
    installed = request.session.get('org_packages', None)
    if installed is None:
        return HttpResponseRedirect(version.get_installer_url(request))
    metadata = request.session.get('metadata', None)
    if metadata is None:
        return HttpResponseRedirect(version.get_installer_url(request))

    install_map = version_install_map(version, installed, metadata, git_ref, fork)

    if 'org_id' not in oauth:
        org_org(request)

    installation_obj = PackageInstallation(
        package = version.package,
        version = version,
        git_ref = git_ref,
        fork = fork,
        org_id = oauth['org_id'],
        org_type = oauth['org_type'],
        instance_url = oauth['instance_url'],
        status = 'Pending',
        username = oauth['username'],
        install_map = install_map_to_json(install_map),
    )
    installation_obj.save()

    # Temporarily save the needed session variables so background processes can do the work
    session_obj = PackageInstallationSession(
        installation = installation_obj,
        oauth = json.dumps(oauth),
        org_packages = json.dumps(installed),
        metadata = json.dumps(request.session.get('metadata', {})),
    )
    session_obj.save()

    order = 0

    for step in install_map:
        step_obj = PackageInstallationStep(
            installation = installation_obj,
            package = step['version'].package,
            version = step['version'],
            previous_version = step['installed'],
            action = step['action'],
            status = 'Pending',
            order = order,
        )
        order += 1
        if step_obj.action == 'skip':
            step_obj.status = 'Succeeded'
        step_obj.save()

    # Clear out the org_packages and metadata cached in session
    if 'org_packages' in request.session:
        del request.session['org_packages']
    if 'metadata' in request.session:
        del request.session['metadata']

    return HttpResponseRedirect('/mpinstaller/installation/%s' % installation_obj.id)

def installation_overview(request, installation_id):
    installation = get_object_or_404(PackageInstallation, id=installation_id)

    oauth = request.session.get('oauth')

    request.session['mpinstaller_current_version'] = installation.version.id

    redirect = quote(request.build_absolute_uri(request.path))
    if oauth and oauth.get('access_token', None):
        login_url = None
        logout_url = request.build_absolute_uri('/mpinstaller/oauth/logout?redirect=%s' % redirect)
    else:
        login_url = request.build_absolute_uri('/mpinstaller/oauth/login?redirect=%s' % redirect)
        logout_url = None

    status_api_url = request.build_absolute_uri('/api/installations/%s/' % installation.id)

    installer_url = installation.version.get_installer_url()

    data = {
        'installation': installation,
        'version': installation.version,
        'installer_url': installer_url,
        'oauth': request.session.get('oauth',None),
        'login_url': login_url,
        'logout_url': logout_url,
        'content_success': installation.get_content_success(),
        'content_failure': installation.get_content_failure(),
        'base_url': request.build_absolute_uri('/mpinstaller/'),
        'status_api_url': status_api_url,
    }

    return render_to_response('mpinstaller/installation_overview.html', data)

def package_installation_overview(request, installation_id):
    """ Shows information about a package installation """
    installation = get_object_or_404(PackageInstallation, id=installation_id)

    return render_to_response('mpinstaller/package_installation.html', {'installation': installation})
     
def oauth_login(request):
    """ Redirects the user to the appropriate login page for OAuth2 login """
    redirect = request.GET['redirect']

    sandbox = request.GET.get('sandbox', False)
    if sandbox == 'true':
        sandbox = True

    if 'oauth' not in request.session:
        request.session['oauth'] = {}
  
    request.session['oauth']['sandbox'] = sandbox
    request.session.save()

    scope = request.GET.get('scope', quote('full refresh_token'))


    oauth = request.session.get('oauth', None)
    if not oauth or not oauth.get('access_token', None):
        sf = SalesforceOAuth2(settings.MPINSTALLER_CLIENT_ID, settings.MPINSTALLER_CLIENT_SECRET, settings.MPINSTALLER_CALLBACK_URL, sandbox=sandbox)
        request.session['mpinstaller_redirect'] = redirect 
        return HttpResponseRedirect(sf.authorize_url(scope=scope))

    return HttpResponseRedirect(redirect)

def oauth_callback(request):
    """ Handles the callback from Salesforce after a successful OAuth2 login """
    oauth = request.session.get('oauth', {})
    sandbox = oauth.get('sandbox', None)
   
    sf = SalesforceOAuth2(settings.MPINSTALLER_CLIENT_ID, settings.MPINSTALLER_CLIENT_SECRET, settings.MPINSTALLER_CALLBACK_URL, sandbox=sandbox)

    code = request.GET.get('code',None)
    if not code:
        return HttpResponse('ERROR: No code provided')

    resp = sf.get_token(code)

    # Set the response in the session
    oauth.update(resp)
    request.session['oauth'] = oauth
    request.session.save()

    return HttpResponseRedirect(request.build_absolute_uri('/mpinstaller/oauth/post_login'))

def oauth_post_login(request):
    """ After successful oauth login, the user is redirected to this view which shows
        the status of fetching needed info from their org to determine install steps """

    version = None
    version_id = request.session.get('mpinstaller_current_version', None)
    if version_id:
        version = PackageVersion.objects.get(id=version_id)

    redirect = request.session.get('mpinstaller_redirect', None)
    if not redirect and version:
        redirect = version.get_installer_url(request)
        request.session['mpinstaller_redirect'] = redirect
    message = None

    oauth = request.session.get('oauth', None)
    if not oauth or 'access_token' not in oauth:
        return HttpResponse('Unauthorized', status=401)

    # Determine if the oauth access token has expired by doing a simple query via the api
    # If it has expired, refresh the token
    try:
        sf = Salesforce(instance_url = oauth['instance_url'], session_id = oauth['access_token'], sandbox = oauth.get('sandbox',False))
        user_id = oauth['id'].split('/')[-1]
        user = sf.User.get(user_id)
    except SalesforceExpiredSession:
        return HttpResponseRedirect(request.build_absolute_uri('/mpinstaller/oauth/refresh'))

    # Setup the list of actions to take after page load
    actions = []
    actions.append({
        'url': request.build_absolute_uri('/mpinstaller/org/user'),
        'message': 'Fetching user info',
    })
    actions.append({
        'url': request.build_absolute_uri('/mpinstaller/org/org'),
        'message': 'Fetching org info',
    })
    actions.append({
        'url': request.build_absolute_uri('/mpinstaller/org/packages'),
        'message': 'Fetching installed packages',
    })
    if version:
        actions.append({
            'url': request.build_absolute_uri('/mpinstaller/org/condition_metadata/%s' % version.id),
            'message': 'Fetching metadata lists needed by the installation',
        })

    return render_to_response('mpinstaller/oauth_post_login.html', {
        'redirect': redirect, 
        'actions': actions,
        'oauth': oauth,
        'version': version,
    })

def oauth_refresh(request):
    version = None
    version_id = request.session.get('mpinstaller_current_version', None)
    if version_id:
        version = PackageVersion.objects.get(id=version_id)

    installer_url = None
    if version:
        installer_url = version.get_installer_url(request)

    # Attempt to refresh token and recall request
    oauth = request.session.get('oauth',None)
    if oauth is None:
        redirect = quote(installer_url)
        return HttpResponseRedirect(request.build_absolute_uri('/mpinstaller/oauth/login?redirect=%s' % redirect))

    sandbox = oauth.get('sandbox', False)
    sf = SalesforceOAuth2(settings.MPINSTALLER_CLIENT_ID, settings.MPINSTALLER_CLIENT_SECRET, settings.MPINSTALLER_CALLBACK_URL, sandbox=sandbox)
    refresh_response = sf.refresh_token(oauth['refresh_token'])
    if refresh_response.get('access_token', None):
        # Set the new token in the session
        request.session['oauth'].update(refresh_response)
        request.session.save()
    else:
        redirect = quote(installer_url)
        return HttpResponseRedirect(request.build_absolute_uri('/mpinstaller/oauth/logout?redirect=%s' % redirect))

    #redirect = request.session.get('mpinstaller_redirect',None)
    #if redirect is None:
    return HttpResponseRedirect(request.build_absolute_uri('/mpinstaller/oauth/post_login'))
    #else:
        #return HttpResponseRedirect(redirect)

def org_user(request):
    oauth = request.session.get('oauth', None)
    if not oauth or not oauth.get('access_token'):
        return HttpResponse('Unauthorized', status=401)

    # Fetch user info from org
    user = get_oauth_user(oauth)
    oauth['username'] = user['Username']
    oauth['perm_modifyalldata'] = user['Profile']['PermissionsModifyAllData']
    
    request.session['oauth'] = oauth
    return HttpResponse('OK')

def org_org(request):
    oauth = request.session.get('oauth', None)
    if not oauth or not oauth.get('access_token'):
        return HttpResponse('Unauthorized', status=401)

    # Fetch org info from org
    org = get_oauth_org(oauth)
    if org:
        oauth['org_id'] = org['Id']
        oauth['org_name'] = org['Name']
        oauth['org_type'] = org['OrganizationType']
    
        # Append (Sandbox) to org type if sandbox
        if oauth.get('sandbox',False):
            oauth['org_type'] = '%s (Sandbox)' % oauth['org_type']

    request.session['oauth'] = oauth
    return HttpResponse('OK')

def org_packages(request):
    oauth = request.session.get('oauth', None)
    if not oauth or not oauth.get('access_token'):
        return HttpResponse('Unauthorized', status=401)

    # We need to be able to see the org to fetch metadata from it
    if oauth.get('perm_modifyalldata'):
        api = ApiRetrieveInstalledPackages(oauth)
        packages = api()
        if api.oauth != oauth:
            request.session['oauth'] = api.oauth
            request.session.save()
    else:
        packages = {}

    request.session['org_packages'] = packages
    request.session.save()
    return HttpResponse('OK')

def org_condition_metadata(request, version_id):
    oauth = request.session.get('oauth', None)
    if not oauth or not oauth.get('access_token'):
        return HttpResponse('Unauthorized', status=401)

    version = get_object_or_404(PackageVersion, id=version_id)
    metadata = request.session.get('metadata', {})

    # We need to be able to see the org to fetch metadata from it
    if oauth.get('perm_modifyalldata'):
        # Handle conditions on the main version
        for condition in version.conditions.all():
            if not metadata.has_key(condition.metadata_type):
                # Fetch the metadata for this type
                api = ApiListMetadata(oauth, condition.metadata_type, metadata)
                metadata[condition.metadata_type] = api()
                
                if api.oauth != oauth:
                    request.session['oauth'] = api.oauth
                    request.session.save()
                    oauth = request.session['oauth']

        # Handle conditions on any dependent versions
        for dependency in version.dependencies.all():
            for condition in dependency.requires.conditions.all():
                if not metadata.has_key(condition.metadata_type):
                    # Fetch the metadata for this type
                    api = ApiListMetadata(oauth, condition.metadata_type, metadata)
                    metadata[condition.metadata_type] = api()
        
                
                    if api.oauth != oauth:
                        request.session['oauth'] = api.oauth
                        request.session.save()
                        oauth = request.session['oauth']

    request.session['metadata'] = metadata
    request.session.save()
    return HttpResponse('OK')

def oauth_logout(request):
    """ Revoke the login token """
    redirect = request.GET.get('redirect',None)

    oauth = request.session.get('oauth', None)
        
    if oauth:
        if oauth.get('access_token', None):
            sf = SalesforceOAuth2(settings.MPINSTALLER_CLIENT_ID, settings.MPINSTALLER_CLIENT_SECRET, settings.MPINSTALLER_CALLBACK_URL)
            sf.revoke_token(oauth['access_token'])
        del request.session['oauth']

    if request.session.get('org_packages', None) != None:
        del request.session['org_packages']

    if request.session.get('metadata', None) != None:
        del request.session['metadata']

    if 'mpinstaller_redirect' in request.session:
        del request.session['mpinstaller_redirect']

    if 'bypass_sandbox' in request.session:
        del request.session['bypass_sandbox']

    if redirect:
        return HttpResponseRedirect(redirect)

    return HttpResponse('You are now logged out')

def get_oauth_org(oauth):
    """ Fetches the org info from the org """
    if not oauth or not oauth.get('access_token', None):
        return 'Not connected'

    sf = Salesforce(instance_url = oauth['instance_url'], session_id = oauth['access_token'], sandbox = oauth.get('sandbox',False))

    # Parse org id from id which ends in /ORGID/USERID
    org_id = oauth['id'].split('/')[-2]

    #try:
    org = sf.Organization.get(org_id)
    return org

    #except SalesforceResourceNotFound:
        #pass

def get_oauth_user(oauth):
    """ Fetches the user info from the org """
    if not oauth or not oauth.get('access_token', None):
        return 'Not connected'
    sf = Salesforce(instance_url = oauth['instance_url'], session_id = oauth['access_token'], sandbox = oauth.get('sandbox',False))
    # Parse user id from id which ends in /ORGID/USERID
    user_id = oauth['id'].split('/')[-1]

    #user = sf.User.get(user_id)
    res = sf.query("SELECT Id, Username, Profile.PermissionsModifyAllData from User WHERE Id='%s'" % user_id)
    user = res['records'][0];
    return user

    
def package_dependencies(request, namespace, beta=None):
    """ Returns package dependencies as json via GET and updates them via POST """
    package = get_object_or_404(Package, namespace=namespace)

    if request.method == 'POST':
        if not package.key or package.key != request.META.get('HTTP_AUTHORIZATION', None):
            return HttpResponse('Unauthorized', status=401)
        dependencies = json.loads(request.body)
        new_dependencies = package.update_dependencies(beta, dependencies)
        return HttpResponse(json.dumps(new_dependencies), content_type='application/json')
    else:
        # For GET requests, return the current dependencies
        return HttpResponse(json.dumps(package.get_dependencies(beta)), content_type='application/json')

@login_required
def package_stats(request, namespace):
    """ Returns package installation stats """
    package = get_object_or_404(Package, namespace=namespace)
   
    stats = []

    total_count = 0
    by_org = {} 
    by_org_type = {} 
    by_version = {}

    for installation in package.installations.filter(status = 'Succeeded'):
        if installation.org_id not in by_org:
            by_org[installation.org_id] = 0
        if installation.org_type not in by_org_type:
            by_org_type[installation.org_type] = 0
        if installation.version and installation.version.number not in by_version:
            by_version[installation.version.number] = 0

        total_count += 1
        by_org[installation.org_id] += 1
        by_org_type[installation.org_type] += 1
        if installation.version:
            by_version[installation.version.number] += 1

    stats.append('Total Successful: %s' % total_count)
    stats.append('Unique Orgs: %s' % len(by_org.keys()))

    for org_type, count in by_org_type.items():
        stats.append('%s Orgs: %s' % (org_type, count))

    for version, count in by_version.items():
        stats.append('%s: %s' % (version, count))
    
    return HttpResponse('\n'.join(stats))    

org_types_map = {
    'ee': 'Enterprise Edition',
    'ees': 'Enterprise Edition (Sandbox)',
    'de': 'Developer Edition',
}

@login_required
def package_errors(request, namespace=None, version=None):

    parent_package = None
    parent_version = None
    if namespace:
        parent_package = get_object_or_404(Package, namespace=namespace)
    if version:
        parent_version = get_object_or_404(PackageVersion, version=version)

    keyword = request.GET.get('keyword', None)

    has_content = request.GET.get('has_content', None)
    if has_content is not None:
        has_content = has_content in ('1','True','true','t')

    count_min = request.GET.get('count_min', None)
    if count_min is u'':
        count_min = None
    if count_min is not None and count_min != "":
        count_min = int(count_min)

    packages = request.GET.get('packages', None)
    if packages is not None:
        packages = request.GET.getlist('packages')

    versions = request.GET.get('versions', None)
    if versions is not None:
        versions = request.GET.getlist('versions')

    org_types = request.GET.get('org_types', None)
    raw_org_types = org_types
    if org_types is not None:
        org_types = [org_types_map.get(org_type, org_type) for org_type in request.GET.getlist('org_types')]

    date_start = request.GET.get('date_start', None)
    if date_start is not None:
        date_start = datetime.strptime(date_start, '%m/%d/%Y')

    date_end = request.GET.get('date_end', None)
    if date_end is not None:
        date_end = datetime.strptime(date_end, '%m/%d/%Y')

    context = InstallationError.objects.drilldown(
        keyword = keyword,
        has_content = has_content,
        parent_package = parent_package,
        parent_version = parent_version,
        count_min = count_min,
        packages = packages, 
        versions = versions,
        org_types = org_types,
    )

    # Add a value key to the org_types facet with the abbreviation
    for facet in context['facets']['org_types']:
        for org_type_abbr, org_type in org_types_map.items():
            if org_type == facet['org_type']:
                facet['value'] = org_type_abbr
                break

    # Mark selected packages
    for facet in context['facets']['packages']:
        if not packages:
            facet['selected'] = False
            continue
        facet['selected'] = unicode(facet['package']) in packages

    # Mark selected versions
    for facet in context['facets']['versions']:
        if not versions:
            facet['selected'] = False
            continue
        facet['selected'] = unicode(facet['version']) in versions

    # Mark selected org_types
    for facet in context['facets']['org_types']:
        if not org_types:
            facet['selected'] = False
            continue
        facet['selected'] = unicode(facet['value']) in raw_org_types


    context['facet_values'] = {
        'keyword':  keyword,
        'has_content':  has_content,
        'count_min':  count_min,
    }

    return render_to_response('mpinstaller/package_errors.html', context)
