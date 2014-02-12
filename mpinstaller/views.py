import requests
import time
import json
from urllib import quote
from xml.dom.minidom import parseString
from django.conf import settings
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from mpinstaller.auth import SalesforceOAuth2
from mpinstaller.models import Package
from mpinstaller.models import PackageVersion
from mpinstaller.package import PackageZipBuilder

SOAP_DEPLOY = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Header>
    <SessionHeader xmlns="http://soap.sforce.com/2006/04/metadata">
      <sessionId>%(session_id)s</sessionId>
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
      <sessionId>%(session_id)s</sessionId>
    </SessionHeader>
  </soap:Header>
  <soap:Body>
    <checkStatus xmlns="http://soap.sforce.com/2006/04/metadata">
      <asyncProcessId>%(process_id)s</asyncProcessId>
    </checkStatus>
  </soap:Body>
</soap:Envelope>"""

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

def version_install_map(namespace, number):
    version = get_object_or_404(PackageVersion, package__namespace = namespace, number = number)

    packages = []

    for dependency in version.dependencies.all():
        packages.append({
            'package': dependency.requires.package.namespace,
            'version': dependency.requires.number,
        })
  
    packages.append({
       'package': version.package.namespace,
       'version': version.number,
    })

    return packages

def oauth_login(request):
    redirect = request.GET['redirect']
   
    oauth = request.session.get('oauth_response', None)
    if not oauth:
        sf = SalesforceOAuth2(settings.MPINSTALLER_CLIENT_ID, settings.MPINSTALLER_CLIENT_SECRET, settings.MPINSTALLER_CALLBACK_URL)
        request.session['mpinstaller_redirect'] = redirect 
        return HttpResponseRedirect(sf.authorize_url())

    return HttpResponseRedirect(redirect)

def oauth_callback(request):
    sf = SalesforceOAuth2(settings.MPINSTALLER_CLIENT_ID, settings.MPINSTALLER_CLIENT_SECRET, settings.MPINSTALLER_CALLBACK_URL)

    code = request.GET.get('code',None)
    if not code:
        return HttpResponse('ERROR: No code provided')

    request.session['oauth_response'] = sf.get_token(code)

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

    endpoint = build_endpoint_url(oauth)

    # Build a zip for the install package
    package_zip = PackageZipBuilder(namespace, number).install_package() 

    # Construct the SOAP envelope message
    session_id = oauth['access_token']   
    message = SOAP_DEPLOY % {'session_id': session_id, 'package_zip': package_zip}
    message = message.encode('utf-8')
    
    headers = {
        'Content-Type': "text/xml; charset=UTF-8",
        'Content-Length': len(message),
        'SOAPAction': 'deploy',
    }

    response = requests.post(url=endpoint, headers=headers, data=message, verify=False)

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

    endpoint = build_endpoint_url(oauth)

    # Build a zip for the install package
    package_zip = PackageZipBuilder(namespace).uninstall_package() 

    # Construct the SOAP envelope message
    session_id = oauth['access_token']   
    message = SOAP_DEPLOY % {'session_id': session_id, 'package_zip': package_zip}
    message = message.encode('utf-8')
    
    headers = {
        'Content-Type': "text/xml; charset=UTF-8",
        'Content-Length': len(message),
        'SOAPAction': 'deploy',
    }

    response = requests.post(url=endpoint, headers=headers, data=message, verify=False)

    id = parseString(response.content).getElementsByTagName('id')[0].firstChild.nodeValue
    return HttpResponse(json.dumps({'process_id': id}), content_type='application/json')

def check_deploy_status(request):
    id = request.GET['id']
    oauth = request.session['oauth_response']
   
    endpoint = build_endpoint_url(oauth)

    # Construct the SOAP envelope message
    session_id = oauth['access_token']   
    message = SOAP_CHECK_STATUS % {'session_id': session_id, 'process_id': id}
    message = message.encode('utf-8')
    
    headers = {
        'Content-Type': "text/xml; charset=UTF-8",
        'Content-Length': len(message),
        'SOAPAction': 'checkStatus',
    }

    response = requests.post(url=endpoint, headers=headers, data=message, verify=False)

    done = parseString(response.content).getElementsByTagName('done')[0].firstChild.nodeValue == 'true'
    state = parseString(response.content).getElementsByTagName('state')[0].firstChild.nodeValue

    return HttpResponse(json.dumps({'done': done, 'state': state}), content_type="application/json")
