import re
import requests
import time
import json
import logging
import base64
import datetime
import dateutil.parser
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
from mpinstaller.utils import zip_subfolder
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
        <ignoreWarnings>true</ignoreWarnings>
        <performRetrieve>false</performRetrieve>
        <purgeOnDelete>%(purge_on_delete)s</purgeOnDelete>
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
        <apiVersion>33.0</apiVersion>
        <unpackaged>
          <types>
            <members>*</members>
            <name>InstalledPackage</name>
          </types>
          <version>33.0</version>
        </unpackaged>
      </retrieveRequest>
    </retrieve>
  </soap:Body>
</soap:Envelope>"""

SOAP_RETRIEVE_PACKAGED = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Header>
    <SessionHeader xmlns="http://soap.sforce.com/2006/04/metadata">
      <sessionId>###SESSION_ID###</sessionId>
    </SessionHeader>
  </soap:Header>
  <soap:Body>
    <retrieve xmlns="http://soap.sforce.com/2006/04/metadata">
      <retrieveRequest>
        <apiVersion>33.0</apiVersion>
        <packageNames>%s</packageNames>
      </retrieveRequest>
    </retrieve>
  </soap:Body>
</soap:Envelope>"""

SOAP_RETRIEVE_UNPACKAGED = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Header>
    <SessionHeader xmlns="http://soap.sforce.com/2006/04/metadata">
      <sessionId>###SESSION_ID###</sessionId>
    </SessionHeader>
  </soap:Header>
  <soap:Body>
    <retrieve xmlns="http://soap.sforce.com/2006/04/metadata">
      <retrieveRequest>
        <apiVersion>33.0</apiVersion>
        <unpackaged>
          %s
        </unpackaged
      </retrieveRequest>
    </retrieve>
  </soap:Body>
</soap:Envelope>"""

SOAP_LIST_METADATA = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Header>
    <SessionHeader xmlns="http://soap.sforce.com/2006/04/metadata">
      <sessionId>###SESSION_ID###</sessionId>
    </SessionHeader>
  </soap:Header>
  <soap:Body>
    <listMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
      <queries>
        <type>%(metadata_type)s</type>
      </queries>
    </listMetadata>
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

def get_element_value(dom, tag):
    """ A simple helper function to fetch the text value of the first element found in an xml document """
    result = dom.getElementsByTagName(tag)
    if result:
        return result[0].firstChild.nodeValue

class BaseMetadataApiCall(object):
    check_interval = 5
    soap_envelope_start = None
    soap_envelope_status = None
    soap_envelope_result = None
    soap_action_start = None
    soap_action_status = None
    soap_action_result = None

    def __init__(self, oauth, installation_step=None, api_version=None):
        self.api_version = api_version if api_version else '33.0'
        self.installation_step = installation_step
        self.oauth = oauth

    def __call__(self):
        self.set_status('InProgress')
        response = self.get_response()
        if self.status != 'Failed':
            return self.process_response(response)

    def set_status(self, status, log=None, private_log=None):
        self.status = status
        self.log = log
        self.private_log = private_log

        if not self.installation_step:
            # return now if there is no installation step object to log to
            return

        self.installation_step.status = self.status
        self.installation_step.log = self.log
        self.installation_step.private_log = self.private_log
        self.installation_step.save()

    def get_response(self):
        if not self.soap_envelope_start:
            raise NotImplemented('No soap_start template was provided')

        # Start the call
        envelope = self.build_envelope_start()
        if not envelope:
            return
        envelope = envelope.encode('utf-8')
        headers = self.build_headers(self.soap_action_start, envelope)
        response = self.call_mdapi(headers, envelope)

        # If no status or result calls are configured, return the result
        if not self.soap_envelope_status and not self.soap_envelope_result:
            return response

        # Process the response to set self.process_id with the process id started
        response = self.process_response_start(response)

        # Check the status if configured
        if self.soap_envelope_status:
            while self.status not in ['Done','Failed']:
                time.sleep(self.check_interval)
                # Check status in a loop until done
                envelope = self.build_envelope_status()
                if not envelope:
                    return
                envelope = envelope.encode('utf-8')
                headers = self.build_headers(self.soap_action_status, envelope)
                response = self.call_mdapi(headers, envelope)
                response = self.process_response_status(response)

            # Fetch the final result and return
            if self.soap_envelope_result:
                envelope = self.build_envelope_result()
                if not envelope:
                    return
                envelope = envelope.encode('utf-8')
                headers = self.build_headers(self.soap_action_result, envelope)
                response = self.call_mdapi(headers, envelope)
            else:
                return response
        else:
            # Check the result and return when done
            while self.status not in ['Succeeded','Failed','Cancelled']:
                time.sleep(self.check_interval)
                envelope = self.build_envelope_result()
                envelope = envelope.encode('utf-8')
                headers = self.build_headers(self.soap_action_result, envelope)
                response = self.call_mdapi(headers, envelope)
                response = process_response_result(response)

        return response
            
    def process_response(self, response):
        return response
    
    def process_response_start(self, response):
        if response.status_code == 500:
            return response
        ids = parseString(response.content).getElementsByTagName('id')
        if ids:
            self.process_id = ids[0].firstChild.nodeValue
        return response

    def process_response_status(self, response):
        done = parseString(response.content).getElementsByTagName('done')
        if done:
            if done[0].firstChild.nodeValue == 'true':
                self.set_status('Done')
        else:
            # If no done element was in the xml, fail logging the entire SOAP envelope as the log
            log = 'An error occurred.  We have logged the error message.  Please contact for support'
            self.set_status('Failed', log, response.content)
        return response

    def process_response_result(self, response):
        self.set_status('Succeeded')
        return response

    def build_envelope_start(self):
        if self.soap_envelope_start:
            return self.soap_envelope_start

    def build_envelope_status(self):
        if self.soap_envelope_status:
            return self.soap_envelope_status % {'process_id': self.process_id}

    def build_envelope_result(self):
        if self.soap_envelope_result:
            return self.soap_envelope_result % {'process_id': self.process_id}

    def build_headers(self, action, message):
        return {
            'Content-Type': "text/xml; charset=UTF-8",
            'Content-Length': len(message),
            'SOAPAction': action,
        }
        
    def build_endpoint_url(self):
        # Parse org id from id which ends in /ORGID/USERID
        org_id = self.oauth['id'].split('/')[-2]
    
        # If "My Domain" is configured in the org, the instance_url needs to be parsed differently
        instance_url = self.oauth['instance_url']
        if instance_url.find('.my.salesforce.com') != -1:
            # Parse instance_url with My Domain configured
            # URL will be in the format https://name--name.na11.my.salesforce.com and should be https://na11.salesforce.com
            instance_url = re.sub(r'https://.*\.(\w+)\.my\.salesforce\.com', r'https://\1.salesforce.com', instance_url)

        # Build the endpoint url from the instance_url
        endpoint = '%s/services/Soap/m/%s/%s' % (instance_url, self.api_version, org_id)
        return endpoint
    
    def call_mdapi(self, headers, envelope, refresh=None):
        # Insert the session id
        session_id = self.oauth['access_token']
        auth_envelope = envelope.replace('###SESSION_ID###', session_id)
       
        response = requests.post(self.build_endpoint_url(), headers=headers, data=auth_envelope, verify=False)
        faultcode = parseString(response.content).getElementsByTagName('faultcode')
    
        # refresh = False can be passed to prevent a loop if refresh fails
        if refresh is None:
            refresh = True
    
        if faultcode:
            return self.handle_soap_error(headers, envelope, refresh, response)

        return response
       
    #@transaction.commit_manually
    def handle_soap_error(self, headers, envelope, refresh, response): 
        # Error in SOAP request, handle the error
        faultcode = parseString(response.content).getElementsByTagName('faultcode')
        if faultcode:
            faultcode = faultcode[0].firstChild.nodeValue
        else:
            faultcode = ''
        faultstring = parseString(response.content).getElementsByTagName('faultstring')
        if faultstring:
            faultstring = faultstring[0].firstChild.nodeValue
        else:
            faultstring = response.content
    
        if faultcode == 'sf:INVALID_SESSION_ID' and self.oauth and self.oauth['refresh_token']:
            # Attempt to refresh token and recall request
            sandbox = self.oauth.get('sandbox', False)
            sf = SalesforceOAuth2(settings.MPINSTALLER_CLIENT_ID, settings.MPINSTALLER_CLIENT_SECRET, settings.MPINSTALLER_CALLBACK_URL, sandbox=sandbox)
            refresh_response = sf.refresh_token(self.oauth['refresh_token'])
            if refresh_response.get('access_token', None):
                # Set the new token in the session
                self.oauth.update(refresh_response)
                
                if refresh:
                    return self.call_mdapi(headers, envelope, refresh=False)
    
        # Log the error on the PackageInstallation
        self.set_status('Failed', '%s: %s' % (faultcode, faultstring))
        
        # No automated error handling possible, return back the raw response
        return response

class ApiRetrieveUnpackaged(BaseMetadataApiCall):
    check_interval = 1
    soap_envelope_start = SOAP_RETRIEVE_INSTALLEDPACKAGE
    soap_envelope_status = SOAP_CHECK_STATUS
    soap_envelope_result = SOAP_CHECK_RETRIEVE_STATUS
    soap_action_start = 'retrieve'
    soap_action_status = 'checkStatus'
    soap_action_result = 'checkRetrieveStatus'

    def __init__(self, oauth, installation_step=None):
        super(ApiRetrieveUnpackaged, self).__init__(oauth, installation_step=installation_step)

        self.metadata_zip = None

    


class ApiRetrieveInstalledPackages(BaseMetadataApiCall):
    check_interval = 1
    soap_envelope_start = SOAP_RETRIEVE_INSTALLEDPACKAGE
    soap_envelope_status = SOAP_CHECK_STATUS
    soap_envelope_result = SOAP_CHECK_RETRIEVE_STATUS
    soap_action_start = 'retrieve'
    soap_action_status = 'checkStatus'
    soap_action_result = 'checkRetrieveStatus'

    def __init__(self, oauth, installation_step=None):
        super(ApiRetrieveInstalledPackages, self).__init__(oauth, installation_step=installation_step)
        self.packages = []

    def process_response(self, response):
        # Parse the metadata zip file from the response
        zipstr = parseString(response.content).getElementsByTagName('zipFile')
        if zipstr:
            zipstr = zipstr[0].firstChild.nodeValue
        else:
            return self.packages
        zipfp = TemporaryFile()
        zipfp.write(base64.b64decode(zipstr))
        zipfile = ZipFile(zipfp, 'r')
    
        packages = {}
    
        # Loop through all files in the zip skipping anything other than InstalledPackages
        for path in zipfile.namelist():
            if not path.endswith('.installedPackage'):
                continue
            namespace = path.split('/')[-1].split('.')[0]
            version = parseString(zipfile.open(path).read()).getElementsByTagName('versionNumber')
            if version:
                version = version[0].firstChild.nodeValue
    
            packages[namespace] = version

        self.packages = packages
        return self.packages

class ApiRetrievePackaged(BaseMetadataApiCall):
    check_interval = 1
    soap_envelope_start = SOAP_RETRIEVE_PACKAGED
    soap_envelope_status = SOAP_CHECK_STATUS
    soap_envelope_result = SOAP_CHECK_RETRIEVE_STATUS
    soap_action_start = 'retrieve'
    soap_action_status = 'checkStatus'
    soap_action_result = 'checkRetrieveStatus'

    def __init__(self, oauth, package_name, installation_step=None):
        super(ApiRetrievePackaged, self).__init__(oauth, installation_step=installation_step)
        self.package_name = package_name

    def build_envelope_start(self):
        return self.soap_envelope_start % self.package_name

    def process_response(self, response):
        # Parse the metadata zip file from the response
        zipstr = parseString(response.content).getElementsByTagName('zipFile')
        if zipstr and zipstr[0].firstChild:
            zipstr = zipstr[0].firstChild.nodeValue
        else:
            raise ValueError(response.content)
        zipfp = TemporaryFile()
        zipfp.write(base64.b64decode(zipstr))

        zipfile = ZipFile(zipfp, 'r')

        return zipfile

class ApiDeploy(BaseMetadataApiCall):
    soap_envelope_start = SOAP_DEPLOY
    soap_envelope_status = SOAP_CHECK_DEPLOY_STATUS
    soap_action_start = 'deploy'
    soap_action_status = 'checkDeployStatus'

    def __init__(self, oauth, package_zip, installation_step, purge_on_delete=True, api_version=None):
        super(ApiDeploy, self).__init__(oauth, installation_step, api_version)
        self.set_purge_on_delete(purge_on_delete)
        self.package_zip = package_zip

    def set_purge_on_delete(self, purge_on_delete):
        if purge_on_delete == False or purge_on_delete == 'false':
            self.purge_on_delete = 'false'
        else:
            self.purge_on_delete = 'true'

        # Disable purge on delete entirely for non sandbox or DE orgs as it is not allowed
        org_type = self.oauth.get('org_type')
        if org_type.find('Sandbox') == -1 and org_type != 'Developer Edition':
            self.purge_on_delete = 'false'

    def build_envelope_start(self):
        if self.package_zip:
            return self.soap_envelope_start % {'package_zip': self.package_zip, 'purge_on_delete': self.purge_on_delete}

    def process_response(self, response):
        status = parseString(response.content).getElementsByTagName('status')
        if status:
            status = status[0].firstChild.nodeValue
        else:
            # If no status element is in the result xml, return fail and log the entire SOAP envelope in the log
            self.set_status('Failed', response.content)
            return self.status
        # Only done responses should be passed so we need to handle any status related to done
        if status in ['Succeeded','SucceededPartial']:
            self.set_status('Succeeded')
        else:
            # If failed, parse out the problem text and set as the log
            problems = parseString(response.content).getElementsByTagName('problem')
            messages = []
            for problem in problems:
                messages.append(problem.firstChild.nodeValue)

            # Parse out any failure text (from test failures in production deployments) and add to log
            failures = parseString(response.content).getElementsByTagName('failures')
            for failure in failures:
                # Get needed values from subelements
                namespace = failure.getElementsByTagName('namespace')
                if namespace and namespace[0].firstChild:
                    namespace = namespace[0].firstChild.nodeValue
                else:
                    namespace = None

                stacktrace = failure.getElementsByTagName('stackTrace')
                if stacktrace and stacktrace[0].firstChild:
                    stacktrace = stacktrace[0].firstChild.nodeValue
                else:
                    stacktrace = None

                message = ['Apex Test Failure: ',]
                if namespace:
                    message.append('from namespace %s: ' % namespace)
                if stacktrace:
                    message.append(stacktrace)

                messages.append(''.join(message))

            if messages:
                log = '\n\n'.join(messages)
            else:
                log = response.content

            self.set_status('Failed', log)
        return self.status
            
            
class ApiInstallVersion(ApiDeploy):
    def __init__(self, oauth, version, installation_step, purge_on_delete=False):
        self.version = version

        # Construct and set the package_zip file
        self.api_version = version.api_version if version.api_version else '33.0'
        if self.version.number:
            self.package_zip = PackageZipBuilder(self.version.package.namespace, self.version.number).install_package()
        elif self.version.zip_url or self.version.repo_url:
            if self.version.repo_url:
                repo_url = self.version.repo_url
                git_ref = self.version.branch
                if installation_step.installation.git_ref:
                    git_ref = installation_step.installation.git_ref
                if installation_step.installation.fork:
                    repo_url_parts = repo_url.split('/')
                    repo_url_parts[3] = installation_step.installation.fork
                    repo_url = '/'.join(repo_url_parts)
                zip_url = '%s/archive/%s.zip' % (repo_url, git_ref)
            else:
                zip_url = self.version.zip_url

            # Deploy a zipped bundled downloaded from a url
            kwargs = {}
            if installation_step.version.github_username and installation_step.version.github_password:
                kwargs['auth'] = requests.auth.HTTPBasicAuth(
                    installation_step.version.github_username,
                    installation_step.version.github_password,
                )
            try:
                zip_resp = requests.get(zip_url, **kwargs)
            except:
                raise ValueError('Failed to fetch zip from %s' % self.version.zip_url)

            zipfp = TemporaryFile()
            zipfp.write(zip_resp.content)
            zipfile = ZipFile(zipfp, 'r')

            if not self.version.subfolder and not self.version.repo_url:
                zipfile.close()
                zipfp.seek(0)
                self.package_zip = base64.b64encode(zipfp.read())
            else:
                ignore_prefix = ''
                if self.version.repo_url:
                    # Get the top level folder from the zip
                    ignore_prefix = '%s/' % zipfile.namelist()[0].split('/')[0]
                
                # Extract a subdirectory from the zip
                subdirectory = ignore_prefix + self.version.subfolder
                subzip = zip_subfolder(zipfile, subdirectory, self.version.namespace_token, self.version.namespace)
                subzipfp = subzip.fp
                subzip.close()
                subzipfp.seek(0)
                self.package_zip = base64.b64encode(subzipfp.read())

        super(ApiInstallVersion, self).__init__(oauth, self.package_zip, installation_step, purge_on_delete=purge_on_delete, api_version=self.api_version)

class ApiUninstallVersion(ApiDeploy):
    def __init__(self, oauth, version, installation_step, purge_on_delete=True):
        self.version = version

        if not version.number:
            self.package_zip = None
        else:
            self.package_zip = PackageZipBuilder(self.version.package.namespace).uninstall_package()
        super(ApiUninstallVersion, self).__init__(oauth, self.package_zip, installation_step, purge_on_delete)

class ApiListMetadata(BaseMetadataApiCall):
    soap_envelope_start = SOAP_LIST_METADATA
    soap_action_start = 'listMetadata'

    def __init__(self, oauth, metadata_type, metadata, installation_step=None):
        super(ApiListMetadata, self).__init__(oauth, installation_step)
        self.metadata_type = metadata_type
        self.metadata = metadata

    def build_envelope_start(self):
        return self.soap_envelope_start % {'metadata_type': self.metadata_type}

    def process_response(self, response):
        metadata = []

        tags = [
            'createdById',
            'createdByName',
            'createdDate',
            'fileName',
            'fullName',
            'id',
            'lastModifiedById',
            'lastModifiedByName',
            'lastModifiedDate',
            'manageableState',
            'namespacePrefix',
            'type',
        ]
    
        # These tags will be interpreted into dates
        parse_dates = [
            'createdDate',
            'lastModifiedDate',
        ]
        
        for result in parseString(response.content).getElementsByTagName('result'):
            result_data = {}
    
            # Parse fields
            for tag in tags:
                result_data[tag] = get_element_value(result, tag)
    
            # Parse dates 
            # FIXME: This was breaking things
            #for key in parse_dates:
            #    if result_data[key]:
            #        result_data[key] = dateutil.parser.parse(result_data[key])
    
            metadata.append(result_data)
   
        self.metadata[self.metadata_type] = metadata
        return metadata
