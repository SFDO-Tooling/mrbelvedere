import logging
import json
import requests
import urllib
from distutils.version import LooseVersion
from mpinstaller.models import Package
from mpinstaller.models import PackageVersion
from mpinstaller.github import github_api

logger = logging.getLogger(__name__)

def list_github_directories(owner, repo, path, ref=None, username=None, password=None):
    subdirs = []

    if ref:
        path += '?ref=%s' % urllib.quote(ref)
    dirlist = github_api(owner, repo, '/contents%s' % path, username=username, password=password)


    if 'message' in dirlist:
        # If the path was not found, return an empty list
        if dirlist['message'] == 'Not Found':
            return subdirs

        # Otherwise, we hit a real error and need to raise it
        raise ValueError(dirlist['message'])
   
    for item in dirlist:
        # Skip files, we only want directories
        if item['type'] != 'dir':
            continue
        subdirs.append(item['name'])
    
    return subdirs

class MockVersionAllDependencies(object):
    """ Mocks a PackageVersion and its dependencies to avoid the need to create dependencies in the db """
    
    def __init__(self, dependencies):
        self.dependencies = []
        for dependency in dependencies:
            self.dependencies.append(MockVersionDependency(dependency))

    def __call__(self):
        return self.dependencies

class MockVersionDependency(object):
    """ Represents a single mock PackageVersionDependency """

    def __init__(self, dependency):
        self.requires = dependency['package_version']
        self.order = dependency['order']
        self.option_type = dependency['option_type']
    
def create_repo_package_versions(version, git_ref=None, fork=None):
    """ Creates all dependent PackageVersion objects from a PackageVersion with a repo_url """

    # If there is no repo_url on the PackageVersion, do nothing
    if not version.repo_url:
        return

    repo_url = version.repo_url
    if fork:
        repo_url_parts = repo_url.split('/')
        repo_url_parts[3] = fork
        repo_url = '/'.join(repo_url_parts)

    # Set up the urls to fetch the dependency files from the repo
    if not git_ref:
        git_ref = version.branch
    raw_url_base = repo_url.replace('https://github.com','https://raw.githubusercontent.com')
    file_url = '%s/%s/' % (raw_url_base, git_ref)

    # Parse the owner and repo from the url
    owner, repo = repo_url.split('/')[3:5]
  
    # Get the contents of version.properties if it exists 
    try:
        version_properties = requests.get(file_url + 'version.properties').content
    except:
        version_properties = None

    required_packages = {}
    package_order = []

    if version_properties:
        for line in version_properties.split('\n'):
            if line.find('=') == -1:
                continue

            key, value = line.split('=')
            key = key.strip()
            value = value.strip()

            if key == 'required.packages':
                package_order = value.split(',')
                package_order = [package.strip() for package in package_order if package != 'managed']
                continue

            if key == 'version.managed':
                continue

            key = key.replace('version.','')

            required_packages[key] = value

    # Find all the unpackaged subdirectories that need to be deployed
    unpackaged = list_github_directories(owner, repo, '/unpackaged', git_ref, version.github_username, version.github_password) 
    unpackaged_subdirs = {}
    for item in unpackaged:
        if item in ('pre','post'):
            unpackaged_subdirs[item] = []
        else:
            unpackaged_subdirs[item] = {}

    for subdir in unpackaged_subdirs.keys():
        subdir_contents = list_github_directories(owner, repo, '/unpackaged/%s' % subdir, git_ref, version.github_username, version.github_password)
        for item in subdir_contents:
            # For unpackaged/pre and unpackaged/post, simply include subdirectories
            if subdir in ('pre','post'):
                unpackaged_subdirs[subdir].append(item)
                continue

            # For all other directories, assume they are namespace pre/post directories
            if subdir not in required_packages:
                # Skip any namespaces not in required_packages
                continue

            # If this is a namespace pre/post for a required namespace, get the contents of its subfolders
            if item not in unpackaged_subdirs[subdir]:
                unpackaged_subdirs[subdir][item] = []
 
            subsubdir_contents = list_github_directories(owner, repo, '/unpackaged/%s/%s' % (subdir, item), git_ref, version.github_username, version.github_password)
            for subitem in subsubdir_contents:
                unpackaged_subdirs[subdir][item].append(subitem)

    # Sort the subdirs
    for subdir in unpackaged_subdirs.keys():
        if subdir in ('pre','post'):
            unpackaged_subdirs[subdir].sort()
            continue
        for subsubdir in subdir.keys():
            unpackaged_subdirs[subdir][subsubdir].sort()

    # Assemble a linear order of dependencies
    dependencies = []
    counter_pre = 1
    counter_post = 100
    
    # Add all package dependencies and their pre/post bundles   
    for package in package_order:
        pre = unpackaged_subdirs.get(package, {}).get('pre',None)
        post = unpackaged_subdirs.get(package, {}).get('post',None)

        # Handle pre bundles for the namespace
        if pre:
            subfolder = 'unpackaged/%s/pre' % package
            for bundle in pre:
                dependencies.append({
                    'namespace': '%s_%s_%s_pre_%s' % (owner, repo, package, bundle),
                    'name': '%s/%s' % (subfolder, bundle),
                    'repo_url': version.repo_url,
                    'subfolder': '%s/%s' % (subfolder, bundle),
                    'branch': version.branch,
                    'order': counter_pre,
                    'option_type': 'default',
                })

        # Handle the namespace package
        version_number = required_packages.get(package, 'Not Installed')
        dependencies.append({
            'namespace': package,
            'name': version_number,
            'number': version_number,
            'order': counter_pre,
            'option_type': 'default',
        })

        # Handle post bundles for the namespace
        if post:
            subfolder = 'unpackaged/%s/post' % package
            for bundle in post:
                dependencies.append({
                    'namespace': '%s_%s_%s_post_%s' % (owner, repo, package, bundle),
                    'name': '%s/%s' % (subfolder, bundle),
                    'namespace_token': '%%%NAMESPACE%%%',
                    'namespace_replace': package,
                    'repo_url': version.repo_url,
                    'subfolder': '%s/%s' % (subfolder, bundle),
                    'branch': version.branch,
                    'order': counter_pre,
                    'option_type': 'default',
                })

        counter_pre += 1

    if 'pre' in unpackaged_subdirs:
        for bundle in unpackaged_subdirs['pre']:
            subfolder = 'unpackaged/pre/%s' % bundle
            dependencies.append({
                'namespace': '%s_%s_pre_%s' % (owner, repo, bundle),
                'name': subfolder,
                'repo_url': version.repo_url,
                'subfolder': subfolder,
                'branch': version.branch,
                'order': counter_pre,
                'option_type': 'default',
            })
            counter_pre += 1

    if 'post' in unpackaged_subdirs:
        for bundle in unpackaged_subdirs['post']:
            subfolder = 'unpackaged/post/%s' % bundle
            dependencies.append({
                'namespace': '%s_%s_post_%s' % (owner, repo, bundle),
                'name': subfolder,
                'namespace_token': '%%%NAMESPACE%%%',
                'repo_url': version.repo_url,
                'subfolder': subfolder,
                'branch': version.branch,
                'order': counter_post,
                'option_type': 'optional',
            })
            counter_post += 1
    

    # Now, get or create the Package and PackageVersions for the dependencies
    for dependency in dependencies:
        package, created = Package.objects.get_or_create(
            namespace = dependency['namespace'],
            defaults = {'name': dependency['name']},
        )
        if 'number' in dependency:
            package_version, created = PackageVersion.objects.get_or_create(
                package = package,
                number = dependency['number'],
                defaults = {'name': dependency['name']},
            )
        else:
            package_version, created = PackageVersion.objects.get_or_create(
                package = package,
                repo_url = dependency['repo_url'],
                subfolder = dependency['subfolder'],
                branch = dependency['branch'],
                namespace_token = dependency.get('namespace_token', None),
                namespace = dependency.get('namespace_replace', None),
                defaults = {'name': dependency['name']},
            )
        dependency['package'] = package
        dependency['package_version'] = package_version

    # Finally, build a MockVersionAllDependencies object to override the all method on dependencies
    return MockVersionAllDependencies(dependencies)


def version_install_map(version, installed=None, metadata=None, git_ref=None, fork=None):

    if not installed:
        installed = {}
    if not metadata:
        metadata = {}

    packages = []
    packages_post = []
    uninstalled = []

    if version.repo_url:
        dependencies = create_repo_package_versions(version, git_ref, fork)()
    else:
        dependencies = version.dependencies.all()

    # First, check for any dependent packages which need to be uninstalled
    child_uninstalled = False
    for dependency in dependencies:
        installed_version = None

        namespace = dependency.requires.package.namespace
        requested_version = dependency.requires.number

        # If there is no requested version, there is no need to uninstall
        if not requested_version:
            continue

        if installed:
            installed_version = installed.get(namespace, None)
        if not installed_version:
            continue

        uninstall = False
        if child_uninstalled:
            uninstall = True
        elif installed_version == requested_version:
            continue
        elif installed_version.find('Beta') != -1:
            if installed_version != requested_version:
                uninstall = True
        elif requested_version.find('Beta') == -1:
            installed_version_f = LooseVersion(installed_version)
            requested_version_f = LooseVersion(requested_version)
            if installed_version_f > requested_version_f:
                uninstall = True

        if not uninstall:
            continue

        child_uninstalled = True
        uninstalled.append(namespace)

        if dependency.order < 100:
            packages.append({
                'version': dependency.requires,
                'option_type': dependency.option_type,
                'installed': installed_version,
                'action': 'uninstall',
            })
        else:
            packages_post.append({
                'version': dependency.requires,
                'option_type': dependency.option_type,
                'installed': installed_version,
                'action': 'uninstall',
            })

    # Next, check if the main package needs uninstalled
    installed_version = None

    uninstall = False
    if installed:
        installed_version = installed.get(version.package.namespace, None)
    if installed_version and version.number:
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
            'version': version,
            'option_type': 'required',
            'installed': installed_version,
            'action': 'uninstall',
        })

    # Include any post installation packages which need uninstall
    if packages_post:
        packages.extend(packages_post)
        packages_post = []

    # Reverse the uninstall order to uninstall parents first
    if packages:
        packages.reverse()

   
    # Next, check for dependent packages which need to be installed 
    for dependency in dependencies:
        installed_version = None

        namespace = dependency.requires.package.namespace
        requested_version = dependency.requires.number

        # Check if the org matches all metadata conditions for the version
        passes_conditions = dependency.requires.check_conditions(metadata)
    
        if installed:
            installed_version = installed.get(dependency.requires.package.namespace, None)
    
        if not passes_conditions or (installed_version and namespace not in uninstalled):
            if not passes_conditions or installed_version == requested_version:
                if dependency.order < 100:
                    packages.append({
                        'version': dependency.requires,
                        'option_type': dependency.option_type,
                        'installed': installed_version,
                        'action': 'skip',
                    })
                else:
                    packages_post.append({
                        'version': dependency.requires,
                        'option_type': dependency.option_type,
                        'installed': installed_version,
                        'action': 'skip',
                    })
                continue

        if dependency.order < 100:
            packages.append({
                'version': dependency.requires,
                'option_type': dependency.option_type,
                'installed': installed_version,
                'action': 'install',
            })
        else:
            packages_post.append({
                'version': dependency.requires,
                'option_type': dependency.option_type,
                'installed': installed_version,
                'action': 'install',
            })

    # Finally, check if the main package needs to be installed
    installed_version = None

    if installed:
        installed_version = installed.get(version.package.namespace, None)

    # Check if the org matches all metadata conditions for the version
    passes_conditions = version.check_conditions(metadata)

    if passes_conditions:
        if installed_version != version.number:
            packages.append({
                'version': version,
                'option_type': 'required',
                'installed': installed_version,
                'action': 'install',
            })
        # If this is not a managed package, always install it
        elif not version.number:
            packages.append({
                'version': version,
                'option_type': 'required',
                'installed': installed_version,
                'action': 'install',
            })
        # Otherwise, skip the main package
        else:
            packages.append({
                'version': version,
                'option_type': 'required',
                'installed': installed_version,
                'action': 'skip',
            })
    else:
        packages.append({
            'version': version,
            'option_type': 'required',
            'installed': installed_version,
            'action': 'skip',
        })

    # Include any post installation packages which need uninstall
    if packages_post:
        packages.extend(packages_post)
        packages_post = []

    return packages


def install_map_to_package_list(install_map):
    namespaces = {}

    # Build a list of all packages which will be uninstalled
    uninstalled = [] 
    for step in install_map:
        if step['action'] == 'uninstall':
            uninstalled.append(step['version'].package.namespace)

    # Build a dictionary by namespace with the needed info
    for step in install_map:
        package = step['version'].package
        if not namespaces.has_key(package.namespace):
            namespaces[package.namespace] = {
                'package': package.name,
                'description': package.description,
                'install': False,
                'upgrade': False,
                'uninstall': False,
                'skip': False,
                'default_checked': True,
                'namespace': package.namespace,
                'installed': step['installed'],
                'version': step['version'],
                'option_type': step['option_type'],
            }

        # Set the install, upgrade, uninstall, and skip values
        if step['action'] == 'install':
            # Is this an install or upgrade?
            if step['installed'] and package.namespace not in uninstalled:
                namespaces[package.namespace]['upgrade'] = True
            else:
                namespaces[package.namespace]['install'] = True
        if step['action'] == 'uninstall':
            namespaces[package.namespace]['uninstall'] = True

        if not namespaces[package.namespace]['uninstall'] and not namespaces[package.namespace]['install'] and not namespaces[package.namespace]['upgrade']:
            namespaces[package.namespace]['skip'] = True
            namespaces[package.namespace]['default_checked'] = False

    # Convert the dictionary into an ordered list for use in templates.
    namespaces_list = []
    for step in install_map:
        # Skip uninstalls as we are only interested in order of install
        if step['action'] == 'uninstall':
            continue
        package = step['version'].package
        namespace = namespaces[package.namespace]
        namespaces_list.append(namespaces[package.namespace])
            
    return namespaces_list

def install_map_to_json(install_map):
    install_map_clean = []
    for step in install_map:
        step_clean = step.copy()
        step_clean['version'] = step['version'].id
        install_map_clean.append(step_clean)
    return json.dumps(install_map_clean)

def json_to_install_map(data):
    install_map = json.loads(data)
    for step in install_map:
        step['version'] = Version.objects.get(step['version'])
    return install_map
