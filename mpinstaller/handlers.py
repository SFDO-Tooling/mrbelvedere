import json
from django.db.models.signals import post_save
from django.dispatch import receiver
from time import sleep
import django_rq
from mpinstaller.models import PackageInstallation, PackageInstallationStep
from mpinstaller.mdapi import ApiInstallVersion, ApiUninstallVersion

@receiver(post_save, sender=PackageInstallationStep)
def set_installation_status(sender, **kwargs):
    step = kwargs['instance']

    # Always set installation to failed and all other pending steps to cancelled if the step failed
    if step.status == 'Failed' and step.installation.status != 'Failed':
        step.installation.status = 'Failed'
        step.installation.log = 'Failed to %s package version %s' % (step.action, step.version.name)
        step.installation.save()

        # Set all other installs to 'Cancelled'
        for sibling_step in step.installation.steps.filter(status = 'Pending'):
            sibling_step.status = 'Cancelled'
            sibling_step.log = 'Cancelled due to failure in step %s' % step
            sibling_step.save()
        
        return
   
    # Set installation to InProgress if a step has started and the current installation status is Pending 
    if step.status == 'InProgress' and step.installation.status == 'Pending':
        step.installation.status = 'InProgress'
        step.installation.save()
        return
       
    # When a step succeeds, check if all steps have succeeded and set installation status if so 
    if step.status == 'Succeeded' and step.installation.status == 'InProgress':
        all_succeeded = True
        for inst_step in step.installation.steps.all():
            if inst_step.status != 'Succeeded':
                all_succeeded = False
                break
           
        if all_succeeded: 
            step.installation.status = 'Succeeded'
            step.installation.log = 'The package %s was installed successfully' % step.installation.version
            step.installation.save()
            return
   
    # If a step was skipped, mark the installation as InProgress 
    if step.status == 'Succeeded' and step.action != 'skip' and step.installation.status == 'Pending':
        step.installation.status = 'InProgress'
        step.installation.save()
        return

@receiver(post_save, sender=PackageInstallation)
def queue_installation(sender, **kwargs):
    if not kwargs['created']:
        # Only run on create
        return
    install_package_version.delay(kwargs['instance'].id)

@django_rq.job('default', timeout=1800)
def install_package_version(installation_id):
    """ Installs a PackageVersion and its dependencies into an org using a PackageInstallationSession for authentication """

    session = None
    
    # Wrap everything in try so we can use finally to delete the session at the end no matter what happens
    try:
        # Get the installation from the database
        try:
            installation = PackageInstallation.objects.get(id = installation_id)
        except PackageInstallation.DoesNotExist:
            return 'Error: No installation found with id %s' % installation_id

        # Only execute pending installations
        if installation.status != 'Pending':
            return 'Skipping: Installation %s is already %s' % (installation_id, installation.status)

        # Look for a session, error if none found
        session = installation.sessions.all()[0]
        if not session:
            installation.status = 'Failed'
            installation.log = 'No session found for installation with id %s' % installation_id
            installation.save()
            return '%s: %' % (installation.status, installation.log)

        oauth = json.loads(session.oauth)
        org_packages = json.loads(session.org_packages)
        metadata = json.loads(session.metadata)

        step = None
        # Loop through the steps and install each package
        for step in installation.steps.filter(status = 'Pending'):
            try:
                if step.action == 'skip':
                    continue

                installation.log = 'Running Step: %s' % step
                installation.save()
                
                if step.action in ['install','upgrade']:
                    api = ApiInstallVersion(oauth, step.version, step)
                    api()
                    if api.status == 'Failed':
                        # Marking the installation as failed is done by another handler
                        return 'Failed: Step for %s failed' % step.version
                elif step.action == 'uninstall':
                    api = ApiUninstallVersion(oauth, step.version, step)
                    api()
                    if api.status == 'Failed':
                        # Marking the installation as failed is done by another handler
                        return 'Failed: Step for %s failed' % step.version
            except Exception, e_step :
                step.status = 'Failed'    
                step.log = str(e_step)
                step.save()
                raise e_step
    
        return 'DONE'

    except Exception, e:
        installation.status = 'Failed'    
        installation.log = str(e)
        installation.save()
        return 'Failed: %s' % installation.log

    finally:
        # Always delete the session which contains oauth info
        if session:
            session.delete()
