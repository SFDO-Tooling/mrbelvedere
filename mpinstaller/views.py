import requests
import time
import json
from urllib import quote
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

SOAP_CHECK_STATUS = """<?xml version="1.0" encoding="utf-8"?>
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

    install_map_prod = []
    if package.current_prod:
        install_map_prod = version_install_map(namespace, package.current_prod.number)

    install_map_beta = []
    if package.current_beta:
        install_map_beta = version_install_map(namespace, package.current_beta.number)

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
        'install_map_prod': install_map_prod,
        'install_map_beta': install_map_beta,
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

    # Build the endpoint url from the instance_url
    endpoint_base = oauth['instance_url'].replace('.salesforce.com','-api.salesforce.com')
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
    
def version_install_map(namespace, number):
    version = get_object_or_404(PackageVersion, package__namespace = namespace, number = number)

    packages = []

    for dependency in version.dependencies.all():
        packages.append({
            'package': dependency.requires.package.name,
            'namespace': dependency.requires.package.namespace,
            'version': dependency.requires.number,
        })
  
    packages.append({
       'package': version.package.name,
       'namespace': version.package.namespace,
       'version': version.number,
    })

    return packages

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
    return HttpResponse(json.dumps({'process_id': id}), content_type='application/json')

def check_deploy_status(request):
    id = request.GET['id']
    oauth = request.session['oauth_response']

    endpoint = build_endpoint_url(oauth)

    # Construct the SOAP envelope message
    session_id = oauth['access_token']   
    message = SOAP_CHECK_STATUS % {'process_id': id}
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
