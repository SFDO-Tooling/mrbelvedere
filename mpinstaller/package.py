from base64 import b64encode
from zipfile import ZipFile
from tempfile import TemporaryFile

PACKAGE_XML = """<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
  <types>
    <members>%s</members>
    <name>InstalledPackage</name>
  </types>
<version>43.0</version>
</Package>"""

EMPTY_PACKAGE_XML = """<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
<version>43.0</version>
</Package>"""

INSTALLED_PACKAGE = """<?xml version="1.0" encoding="UTF-8"?>
<InstalledPackage xmlns="http://soap.sforce.com/2006/04/metadata">
  <versionNumber>%s</versionNumber>
</InstalledPackage>"""

class PackageZipBuilder(object):

    def __init__(self, namespace, version=None):
        self.namespace = namespace
        self.version = version

    def open_zip(self):
        self.zip_file = TemporaryFile()
        self.zip= ZipFile(self.zip_file, 'w')

    def install_package(self):
        self.open_zip()
        if not self.version:
            raise ValueError('You must provide a version to install a package')

        package_xml = PACKAGE_XML % self.namespace
        #package_xml = package_xml.encode('utf-8')
        self.zip.writestr('package.xml', package_xml)

        installed_package = INSTALLED_PACKAGE % self.version
        #installed_package.encode('utf-8')
        self.zip.writestr('installedPackages/%s.installedPackage' % self.namespace, installed_package)

        return self.encode_zip()

    def uninstall_package(self):
        self.open_zip()
        self.zip.writestr('package.xml', EMPTY_PACKAGE_XML)
        self.zip.writestr('destructiveChanges.xml', PACKAGE_XML % self.namespace)
        return self.encode_zip()
        
    def encode_zip(self):
        self.zip.close()
        self.zip_file.seek(0)
        return b64encode(self.zip_file.read())
