import re
import requests
import time
import json
import logging
import base64
from tempfile import TemporaryFile
from zipfile import ZipFile
from urllib import quote
from distutils.version import LooseVersion
from xml.dom.minidom import parseString
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from mpinstaller.auth import SalesforceOAuth2
from mpinstaller.models import Package
from mpinstaller.models import PackageInstallation
from mpinstaller.models import PackageVersion
from mpinstaller.package import PackageZipBuilder
from simple_salesforce import Salesforce

logger = logging.getLogger(__name__)

SOAP_DEPLOY = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Header>
    <SessionHeader xmlns="http://soap.sforce.com/2006/04/metadata">
      <sessionId>###SESSION_ID###</sessionId>
    </SessionHeader>
  </soap:Header>
  <soap:Body>
    <deploy xmlns="http://soap.sforce.com/2006/04/metadata">
      <ZipFile>%(package_zip)s</ZipFile>
      <DeployOptions>
        <allowMissingFiles>false</allowMissingFiles>
        <autoUpdatePackage>false</autoUpdatePackage>
        <checkOnly>false</checkOnly>
        <ignoreWarnings>false</ignoreWarnings>
        <performRetrieve>false</performRetrieve>
        <purgeOnDelete>true</purgeOnDelete>
        <rollbackOnError>true</rollbackOnError>
        <runAllTests>false</runAllTests>
        <singlePackage>true</singlePackage>
      </DeployOptions>
    </deploy>
  </soap:Body>
</soap:Envelope>"""

SOAP_CHECK_DEPLOY_STATUS = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Header>
    <SessionHeader xmlns="http://soap.sforce.com/2006/04/metadata">
      <sessionId>###SESSION_ID###</sessionId>
    </SessionHeader>
  </soap:Header>
  <soap:Body>
    <checkDeployStatus xmlns="http://soap.sforce.com/2006/04/metadata">
      <asyncProcessId>%(process_id)s</asyncProcessId>
      <includeDetails>true</includeDetails>
    </checkDeployStatus>
  </soap:Body>
</soap:Envelope>"""

SOAP_RETRIEVE_INSTALLEDPACKAGE = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Header>
    <SessionHeader xmlns="http://soap.sforce.com/2006/04/metadata">
      <sessionId>###SESSION_ID###</sessionId>
    </SessionHeader>
  </soap:Header>
  <soap:Body>
    <retrieve xmlns="http://soap.sforce.com/2006/04/metadata">
      <retrieveRequest>
        <apiVersion>29.0</apiVersion>
        <unpackaged>
          <types>
            <members>*</members>
            <name>InstalledPackage</name>
          </types>
          <version>29.0</version>
        </unpackaged>
      </retrieveRequest>
    </retrieve>
  </soap:Body>
</soap:Envelope>"""

SOAP_CHECK_STATUS = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Header>
    <SessionHeader xmlns="http://soap.sforce.com/2006/04/metadata">
      <sessionId>###SESSION_ID###</sessionId>
    </SessionHeader>
  </soap:Header>
  <soap:Body>
    <checkStatus xmlns="http://soap.sforce.com/2006/04/metadata">
      <asyncProcessId>%(process_id)s</asyncProcessId>
    </checkStatus>
  </soap:Body>
</soap:Envelope>"""

SOAP_CHECK_RETRIEVE_STATUS = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Header>
    <SessionHeader xmlns="http://soap.sforce.com/2006/04/metadata">
      <sessionId>###SESSION_ID###</sessionId>
    </SessionHeader>
  </soap:Header>
  <soap:Body>
    <checkRetrieveStatus xmlns="http://soap.sforce.com/2006/04/metadata">
      <asyncProcessId>%(process_id)s</asyncProcessId>
    </checkRetrieveStatus>
  </soap:Body>
</soap:Envelope>"""

@transaction.commit_manually
def call_mdapi(request, url, headers, data, refresh=None):
    oauth = request.session.get('oauth_response',None)
    session_id = oauth['access_token']
    
    response = requests.post(url, headers=headers, data=data.replace('###SESSION_ID###', session_id), verify=False)
    faultcode = parseString(response.content).getElementsByTagName('faultcode')

    # refresh = False can be passed to prevent a loop if refresh fails
    if refresh is None:
        refresh = True

    if not faultcode:
        return response
    
    # Error in SOAP request, handle the error
    faultcode = faultcode[0].firstChild.nodeValue
    faultstring = parseString(response.content).getElementsByTagName('faultstring')
    if faultstring:
        faultstring = faultstring[0].firstChild.nodeValue
    else:
        faultstring = ''

    # Log the error on the PackageInstallation
    install_id = request.session.get('mpinstaller_current_install', None)
    if install_id:
        install = PackageInstallation.objects.get(id=install_id)
        install.status = 'SOAP Fault'
        install.log = '%s: %s' % (faultcode, faultstring)
        install.save()
        transaction.commit()
    
    if faultcode == 'sf:INVALID_SESSION_ID' and oauth and oauth['refresh_token']:
        # Attempt to refresh token and recall request
        sandbox = request.session.get('oauth_sandbox', False)
        sf = SalesforceOAuth2(settings.MPINSTALLER_CLIENT_ID, settings.MPINSTALLER_CLIENT_SECRET, settings.MPINSTALLER_CALLBACK_URL, sandbox=sandbox)
        refresh_response = sf.refresh_token(oauth['refresh_token'])
        if refresh_response.get('access_token', None):
            # Set the new token in the session
            request.session['oauth_response'].update(refresh_response)
            
            if refresh:
                return call_mdapi(request, url, headers, data, refresh=False)

    # No automated error handling possible, return back the raw response
    return response

def package_overview(request, namespace):
    package = get_object_or_404(Package, namespace = namespace)

    # If authenticated and session does not have mpinstaller_org_packages, redirect to fetch package versions from org
    oauth = request.session.get('oauth_response')
    if oauth and request.session.get('mpinstaller_org_packages', None) is None:
        request.session['mpinstaller_redirect'] = request.build_absolute_uri(request.path)
        return HttpResponseRedirect(request.build_absolute_uri('/mpinstaller/retrieve_org_packages'))

    installed = request.session.get('mpinstaller_org_packages')

    install_map_prod = []
    package_list_prod = []
    if package.current_prod:
        install_map_prod = version_install_map(namespace, package.current_prod.number, installed)
        package_list_prod = install_map_to_package_list(install_map_prod)

    install_map_beta = []
    package_list_beta = []
    if package.current_beta:
        install_map_beta = version_install_map(namespace, package.current_beta.number, installed)
        package_list_beta = install_map_to_package_list(install_map_beta)

    logged_in = False
    redirect = quote(request.build_absolute_uri(request.path))
    if request.session.get('oauth_response', None):
        login_url = None
        logout_url = request.build_absolute_uri('/mpinstaller/oauth/logout?redirect=%s' % redirect)
    else:
        login_url = request.build_absolute_uri('/mpinstaller/oauth/login?redirect=%s' % redirect)
        logout_url = None

    data = {
        'package': package,
        'oauth': request.session.get('oauth_response',None),
        'login_url': login_url,
        'logout_url': logout_url,
        'base_url': request.build_absolute_uri('/mpinstaller/'),
        'package_list_prod': package_list_prod,
        'package_list_beta': package_list_beta,
        'install_map_prod_json': json.dumps(install_map_prod),
        'install_map_beta_json': json.dumps(install_map_beta),
    }

    return render_to_response('mpinstaller/package_overview.html', data)

def version_overview(request, namespace, number):
    version = get_object_or_404(PackageVersion, package__namespace = namespace, number = number)
    return HttpResponse(version)

def build_endpoint_url(oauth):
    # Parse org id from id which ends in /ORGID/USERID
    org_id = oauth['id'].split('/')[-2]

    # If "My Domain" is configured in the org, the instance_url needs to be parsed differently
    instance_url = oauth['instance_url']
    if instance_url.find('.my.salesforce.com') != -1:
        # Parse instance_url with My Domain configured
        # URL will be in the format https://name--name.na11.my.salesforce.com and should be https://na11.salesforce.com
        instance_url = re.sub(r'https://.*\.(\w+)\.my\.salesforce\.com', r'https://\1.salesforce.com', instance_url)

    # Build the endpoint url from the instance_url
    endpoint_base = instance_url.replace('.salesforce.com','-api.salesforce.com')
    endpoint = '%s/services/Soap/m/29.0/%s' % (endpoint_base, org_id)
    return endpoint

def get_oauth_org(oauth):
    if not oauth:
        return 'Not connected'
    sf = Salesforce(instance_url = oauth['instance_url'], session_id = oauth['access_token'])

    # Parse org id from id which ends in /ORGID/USERID
    org_id = oauth['id'].split('/')[-2]

    org = sf.Organization.get(org_id)
    return org

def get_oauth_user(oauth):
    if not oauth:
        return 'Not connected'
    sf = Salesforce(instance_url = oauth['instance_url'], session_id = oauth['access_token'])
    # Parse user id from id which ends in /ORGID/USERID
    user_id = oauth['id'].split('/')[-1]

    user = sf.User.get(user_id)
    return user

def version_install_map(namespace, number, installed=None):
    version = get_object_or_404(PackageVersion, package__namespace = namespace, number = number)

    packages = []
    uninstalled = []

    # First, check for any dependent packages which need to be uninstalled
    child_uninstalled = False
    for dependency in version.dependencies.all():
        installed_version = None

        namespace = dependency.requires.package.namespace
        requested_version = dependency.requires.number

        if installed:
            installed_version = installed.get(namespace, None)
        if not installed_version:
            continue

        if installed_version == requested_version:
            continue

        uninstall = False
        if child_uninstalled:
            uninstall = True
        elif installed_version.find('Beta') != -1:
            if installed_version != requested_version:
                uninstall = True
        elif requested_version.find('Beta') == -1:
            installed_version_f = LooseVersion(installed_version)
            requested_version_f = LooseVersion(requested_version)
            if installed_version_f < requested_version_f:
                uninstall = True

        if not uninstall:
            continue

        child_uninstalled = True
        uninstalled.append(namespace)

        packages.append({
            'package': dependency.requires.package.name,
            'namespace': namespace,
            'version': requested_version,
            'installed': installed_version,
            'action': 'uninstall',
        })

    # Next, check if the main package needs uninstalled
    installed_version = None

    uninstall = False
    if installed:
        installed_version = installed.get(version.package.namespace, None)
    if installed_version:
        if installed_version.find('Beta') != -1:
            if installed_version != version.number:
                uninstall = True
        else:
            installed_version_f = LooseVersion(installed_version)
            requested_version_f = LooseVersion(version.number)
            if installed_version_f > requested_version_f:
                uninstall = True

    if uninstall:
        packages.append({
            'package': version.package.name,
            'namespace': version.package.namespace,
            'version': version.number,
            'installed': installed_version,
            'action': 'uninstall',
        })

    # Reverse the uninstall order to uninstall parents first
    if packages:
        packages.reverse()

   
    # Next, check for dependent packages which need to be installed 
    for dependency in version.dependencies.all():
        installed_version = None

        namespace = dependency.requires.package.namespace
        requested_version = dependency.requires.number

        if installed:
            installed_version = installed.get(dependency.requires.package.namespace, None)

        if installed_version and namespace not in uninstalled:
            if installed_version == requested_version:
                packages.append({
                    'package': dependency.requires.package.name,
                    'namespace': namespace,
                    'version': requested_version,
                    'installed': installed_version,
                    'action': 'skip',
                })
                continue

        packages.append({
            'package': dependency.requires.package.name,
            'namespace': namespace,
            'version': requested_version,
            'installed': installed_version,
            'action': 'install',
        })

    # Finally, check if the main package needs to be installed
    installed_version = None

    if installed:
        installed_version = installed.get(version.package.namespace, None)
    if installed_version != version.number:
        packages.append({
            'package': version.package.name,
            'namespace': version.package.namespace,
            'version': version.number,
            'installed': installed_version,
            'action': 'install',
        })
    else:
        packages.append({
            'package': version.package.name,
            'namespace': version.package.namespace,
            'version': version.number,
            'installed': installed_version,
            'action': 'skip',
        })

    return packages

def install_map_to_package_list(install_map):
    namespaces = {}
    
    for action in install_map:
        if not namespaces.has_key(action['namespace']):
            namespaces[action['namespace']] = {
                'package': action['package'],
                'install': False,
                'uninstall': False,
                'namespace': action['namespace'],
                'installed': action['installed'],
                'version': action['version'],
            }
        if action['action'] == 'install':
            namespaces[action['namespace']]['install'] = True
        if action['action'] == 'uninstall':
            namespaces[action['namespace']]['uninstall'] = True

    # Convert the dictionary into an ordered list for use in templates.
    namespaces_list = []
    for action in install_map:
        # Skip uninstalls as we are only interested in order of install
        if action['action'] == 'uninstall':
            continue
        namespace = namespaces[action['namespace']]
        namespaces_list.append(namespaces[action['namespace']])
            
    return namespaces_list

def oauth_login(request):
    redirect = request.GET['redirect']

    sandbox = request.GET.get('sandbox', False)
    if sandbox == 'true':
        sandbox = True
  
    request.session['oauth_sandbox'] = sandbox

    oauth = request.session.get('oauth_response', None)
    if not oauth:
        sf = SalesforceOAuth2(settings.MPINSTALLER_CLIENT_ID, settings.MPINSTALLER_CLIENT_SECRET, settings.MPINSTALLER_CALLBACK_URL, sandbox=sandbox)
        request.session['mpinstaller_redirect'] = redirect 
        return HttpResponseRedirect(sf.authorize_url())

    return HttpResponseRedirect(redirect)

def oauth_callback(request):
    sandbox = request.session.get('oauth_sandbox', False)
    sf = SalesforceOAuth2(settings.MPINSTALLER_CLIENT_ID, settings.MPINSTALLER_CLIENT_SECRET, settings.MPINSTALLER_CALLBACK_URL, sandbox=sandbox)

    code = request.GET.get('code',None)
    if not code:
        return HttpResponse('ERROR: No code provided')

    resp = sf.get_token(code)

    # Call the REST API to get the org name for display on screen
    org = get_oauth_org(resp)

    resp['org_id'] = org['Id']
    resp['org_name'] = org['Name']
    resp['org_type'] = org['OrganizationType']

    # Append (Sandbox) to org type if sandbox
    if request.session.get('oauth_sandbox', False):
        resp['org_type'] = '%s (Sandbox)' % resp['org_type']

    # Call the REST API to get the user's login for display on screen
    user = get_oauth_user(resp)
    resp['username'] = user['Username']

    # Log the info
    logger.info(resp)

    # Set the response in the session
    request.session['oauth_response'] = resp

    return HttpResponseRedirect(request.session['mpinstaller_redirect'])

def oauth_logout(request):
    redirect = request.GET['redirect']

    oauth = request.session.get('oauth_response', None)
        
    if oauth:
        sf = SalesforceOAuth2(settings.MPINSTALLER_CLIENT_ID, settings.MPINSTALLER_CLIENT_SECRET, settings.MPINSTALLER_CALLBACK_URL)
        sf.revoke_token(oauth['access_token'])
        del request.session['oauth_response']

    if request.session.get('mpinstaller_org_packages', None) != None:
        del request.session['mpinstaller_org_packages']

    return HttpResponseRedirect(redirect)

def install_package_version(request, namespace, number):
    oauth = request.session.get('oauth_response', None)
    if not oauth:
        raise HttpResponse('Unauthorized', status=401)

    version = get_object_or_404(PackageVersion, package__namespace = namespace, number = number)

    # Log the install
    install = PackageInstallation(
        package = version.package, 
        version = version, 
        action = 'install', 
        username = oauth['username'], 
        org_id = oauth['org_id'],
        org_type = oauth['org_type'],
        status = 'Starting',
    )
    install.save()

    request.session['mpinstaller_current_install'] = install.id

    endpoint = build_endpoint_url(oauth)

    # Build a zip for the install package
    package_zip = PackageZipBuilder(namespace, number).install_package() 

    # Construct the SOAP envelope message
    message = SOAP_DEPLOY % {'package_zip': package_zip}
    message = message.encode('utf-8')
    
    headers = {
        'Content-Type': "text/xml; charset=UTF-8",
        'Content-Length': len(message),
        'SOAPAction': 'deploy',
    }

    response = call_mdapi(request, url=endpoint, headers=headers, data=message)

    id = parseString(response.content).getElementsByTagName('id')[0].firstChild.nodeValue

    # Delete the cached org package versions
    if request.session.get('mpinstaller_org_packages', None) is not None:
        del request.session['mpinstaller_org_packages']

    return HttpResponse(json.dumps({'process_id': id}), content_type='application/json')

def uninstall_package(request, namespace):
    package = get_object_or_404(Package, namespace = namespace)

    oauth = request.session.get('oauth_response', None)
    if not oauth:
        sf = SalesforceOAuth2(settings.MPINSTALLER_CLIENT_ID, settings.MPINSTALLER_CLIENT_SECRET, settings.MPINSTALLER_CALLBACK_URL)
        request.session['mpinstaller_package'] = namespace
        request.session['mpinstaller_version'] = 'uninstall'
        return HttpResponseRedirect(sf.authorize_url())

    # Log the install
    install = PackageInstallation(
        package = package, 
        action = 'uninstall', 
        username = oauth['username'], 
        org_id = oauth['org_id'],
        org_type = oauth['org_type'],
        status = 'Starting',
    )
    install.save()

    request.session['mpinstaller_current_install'] = install.id

    endpoint = build_endpoint_url(oauth)

    # Build a zip for the install package
    package_zip = PackageZipBuilder(namespace).uninstall_package() 

    # Construct the SOAP envelope message
    message = SOAP_DEPLOY % {'package_zip': package_zip}
    message = message.encode('utf-8')
    
    headers = {
        'Content-Type': "text/xml; charset=UTF-8",
        'Content-Length': len(message),
        'SOAPAction': 'deploy',
    }

    response = call_mdapi(request, url=endpoint, headers=headers, data=message)

    id = parseString(response.content).getElementsByTagName('id')[0].firstChild.nodeValue

    # Delete the cached org package versions
    if request.session.get('mpinstaller_org_packages', None) is not None:
        del request.session['mpinstaller_org_packages']

    return HttpResponse(json.dumps({'process_id': id}), content_type='application/json')

def check_deploy_status(request):
    id = request.GET['id']
    oauth = request.session['oauth_response']

    endpoint = build_endpoint_url(oauth)

    # Construct the SOAP envelope message
    session_id = oauth['access_token']   
    message = SOAP_CHECK_DEPLOY_STATUS % {'process_id': id}
    message = message.encode('utf-8')
    
    headers = {
        'Content-Type': "text/xml; charset=UTF-8",
        'Content-Length': len(message),
        'SOAPAction': 'checkDeployStatus',
    }

    response = call_mdapi(request, url=endpoint, headers=headers, data=message)

    done = parseString(response.content).getElementsByTagName('done')[0].firstChild.nodeValue == 'true'
    status = parseString(response.content).getElementsByTagName('status')[0].firstChild.nodeValue

    message = None
    if status == 'Failed':
        message = parseString(response.content).getElementsByTagName('problem')[0].firstChild.nodeValue

    # Update the PackageInstallation status field
    install_id = request.session.get('mpinstaller_current_install', None)
    if install_id:
        install = PackageInstallation.objects.get(id=install_id)
        if install.status != status:
            install.status = status
            install.log = message
            install.save()
        
    data = {
        'done': done,
        'status': status,
        'message': message,
    }

    return HttpResponse(json.dumps(data), content_type="application/json")

def retrieve_org_packages(request):
    oauth = request.session['oauth_response']
    endpoint = build_endpoint_url(oauth)
    
    # Issue a retrieve call
    message = SOAP_RETRIEVE_INSTALLEDPACKAGE.encode('utf-8')

    headers = {
        'Content-Type': "text/xml; charset=UTF-8",
        'Content-Length': len(message),
        'SOAPAction': 'retrieve',
    }

    response = call_mdapi(request, url=endpoint, headers=headers, data=message)

    id = parseString(response.content).getElementsByTagName('id')[0].firstChild.nodeValue

    return HttpResponseRedirect(request.build_absolute_uri('/mpinstaller/retrieve_org_packages/%s' % id))

def retrieve_org_packages_result(request, id):
    oauth = request.session['oauth_response']
    endpoint = build_endpoint_url(oauth)

    # First, use checkStatus to see if the async task is done   
    message = SOAP_CHECK_STATUS % {'process_id': id}
    message = message.encode('utf-8')

    headers = {
        'Content-Type': "text/xml; charset=UTF-8",
        'Content-Length': len(message),
        'SOAPAction': 'checkStatus',
    }

    response = call_mdapi(request, url=endpoint, headers=headers, data=message)
    done = parseString(response.content).getElementsByTagName('done')[0].firstChild.nodeValue
    if done != 'true':
        data = {
            'done': False,
            'id': False,
        }
        # Sleep for 1 second before redirecting for next check
        time.sleep(1)

        return HttpResponseRedirect('/mpinstaller/retrieve_org_packages/%s' % id)


    # If the async task is done, call checkRetrieveStatus to get the results
    message = SOAP_CHECK_RETRIEVE_STATUS % {'process_id': id}
    message = message.encode('utf-8')

    headers = {
        'Content-Type': "text/xml; charset=UTF-8",
        'Content-Length': len(message),
        'SOAPAction': 'checkRetrieveStatus',
    }

    response = call_mdapi(request, url=endpoint, headers=headers, data=message)

    # Parse the metadata zip file from the response
    zipstr = parseString(response.content).getElementsByTagName('zipFile')[0].firstChild.nodeValue
    zipfp = TemporaryFile()
    zipfp.write(base64.b64decode(zipstr))
    zipfile = ZipFile(zipfp, 'r')

    packages = {}

    # Loop through all files in the zip skipping anything other than InstalledPackages
    for path in zipfile.namelist():
        if not path.endswith('.installedPackage'):
            continue
        namespace = path.split('/')[-1].split('.')[0]
        version = parseString(zipfile.open(path).read()).getElementsByTagName('versionNumber')[0].firstChild.nodeValue
        
        packages[namespace] = version

    request.session['mpinstaller_org_packages'] = packages

    return HttpResponseRedirect(request.session.get('mpinstaller_redirect'))
