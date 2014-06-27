import logging
import json
from distutils.version import LooseVersion

logger = logging.getLogger(__name__)

def version_install_map(version, installed=None, metadata=None):

    if not installed:
        installed = {}
    if not metadata:
        metadata = {}

    packages = []
    packages_post = []
    uninstalled = []

    # First, check for any dependent packages which need to be uninstalled
    child_uninstalled = False
    for dependency in version.dependencies.all():
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
                'installed': installed_version,
                'action': 'uninstall',
            })
        else:
            packages_post.append({
                'version': dependency.requires,
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
            'version': version,
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
    for dependency in version.dependencies.all():
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
                        'installed': installed_version,
                        'action': 'skip',
                    })
                else:
                    packages_post.append({
                        'version': dependency.requires,
                        'installed': installed_version,
                        'action': 'skip',
                    })
                continue

        if dependency.order < 100:
            packages.append({
                'version': dependency.requires,
                'installed': installed_version,
                'action': 'install',
            })
        else:
            packages_post.append({
                'version': dependency.requires,
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
                'installed': installed_version,
                'action': 'install',
            })
        # If this is not a managed package, always install it
        elif not version.number:
            packages.append({
                'version': version,
                'installed': installed_version,
                'action': 'install',
            })
        # Otherwise, skip the main package
        else:
            packages.append({
                'version': version,
                'installed': installed_version,
                'action': 'skip',
            })
    else:
        packages.append({
            'version': version,
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
                'namespace': package.namespace,
                'installed': step['installed'],
                'version': step['version'],
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
