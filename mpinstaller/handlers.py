import json
import signal
from rq.worker import signal_name
from django.db.models.signals import pre_save
from django.db.models.signals import post_save
from django.dispatch import receiver
from time import sleep
import django_rq
from mpinstaller.models import PackageInstallation, PackageInstallationStep
from mpinstaller.models import WhiteListOrg
from mpinstaller.mdapi import ApiInstallVersion, ApiUninstallVersion
from mpinstaller.utils import convert_to_18

# Convert all WhiteListOrg.org_id values to 18 character org ids
@receiver(pre_save, sender=WhiteListOrg)
def convert_org_id_to_18(sender, **kwargs):
    org = kwargs['instance']
    if len(org.org_id) == 15:
        org.org_id = convert_to_18(org.org_id)

# Set the error field on a failed step by calling the step's set_error method
@receiver(post_save, sender=PackageInstallationStep)
def set_installation_step_error(sender, **kwargs):
    step = kwargs['instance']
    if step.status == 'Failed' and not step.error:
        step.set_error()

@receiver(post_save, sender=PackageInstallationStep)
def set_installation_status(sender, **kwargs):
    step = kwargs['instance']

    # Always set installation to failed and all other pending steps to cancelled if the step failed
    if step.status == 'Failed' and step.installation.status != 'Failed':
        step.installation.status = 'Failed'
        if step.action == 'uninstall':
            step.installation.log = 'Failed to %s package version %s' % (step.action, step.previous_version)
        else:
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

@django_rq.job('default', timeout=3600)
def install_package_version(installation_id):
    """ Installs a PackageVersion and its dependencies into an org using a PackageInstallationSession for authentication """

    session = None

    # Wrap everything in try so we can use finally to delete the session at the end no matter what happens
    try:
        sleep(3)

        # Get the installation from the database
        try:
            installation = PackageInstallation.objects.get(id = installation_id)
        except PackageInstallation.DoesNotExist:
            return 'Error: No installation found with id %s' % installation_id

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
        for step in installation.steps.filter(status__in = ['Pending','InProgress']):
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
    
        return 'Installation %s: DONE' % installation.id

    except Exception, e:
        installation.status = 'Failed'    
        installation.log = str(e)
        installation.save()
        return 'Failed: %s' % installation.log
