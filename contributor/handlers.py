import json
import signal
import traceback
from rq.worker import signal_name
from django.db.models.signals import post_save
from django.dispatch import receiver
from time import sleep
import django_rq
from contributor.models import Contribution
from contributor.models import ContributionSync
from contributor.models import ContributionSyncError
from mpinstaller.models import PackageInstallation

@receiver(post_save, sender=Contribution)
def queue_sync_contribution(sender, **kwargs):
    sync_contribution.delay(kwargs['instance'].id)

@django_rq.job('default', timeout=1800)
def sync_contribution(contribution_id):

    # Wrap everything so we can capture all exceptions and handle them
    try:
        # Get the Contribution from the database
        try:
            contribution = Contribution.objects.get(id = contribution_id)
        except Contribution.DoesNotExist:
            return 'Error: No Contribution found with id %s' % contribution_id

        changed = False

        # Sync the contribution
        changed = contribution.sync()

        # Save the result if it was changed
        if changed:
            contribution.save()

        return 'Contribution %s synced successfully' % contribution.id

    except Exception, e:
        return 'Failed: %s' % e

@receiver(post_save, sender=ContributionSync)
def queue_commit_from_org(sender, **kwargs):
    if not kwargs['created']:
        return
        
    if kwargs['instance'].message:
        # If a ContributionSync is created with a message value, it is a trigger to commit from org
        commit_from_org.delay(kwargs['instance'].id)

@django_rq.job('default', timeout=1800)
def commit_from_org(contribution_sync_id):
    sync = ContributionSync.objects.get(id = contribution_sync_id)

    sync.contribution.check_sync_state()
    sync.pre_state_behind_main = sync.contribution.state_behind_main
    sync.pre_state_undeployed_commit = sync.contribution.state_undeployed_commit
    sync.pre_state_uncommitted_changes = sync.contribution.state_uncommitted_changes
   
    sync.log += '----- Starting commit from org\n'
    sync.status = 'in_progress'
    sync.save()

    commit = sync.contribution.commit_from_org(message = sync.message)
    if commit:
        sync.log += 'DONE, sha = %s\n' % commit['sha']
        sync.new_commit = commit['sha']
    else:
        sync.log += 'DONE, No changes found\n'
    sync.save()

    sync.log += '----- Checking post sync state\n'
    sync.save()

    sync.contribution.check_sync_state()

    sync.log += 'DONE\n'
    sync.post_state_behind_main = sync.contribution.state_behind_main
    sync.post_state_undeployed_commit = sync.contribution.state_undeployed_commit
    sync.post_state_uncommitted_changes = sync.contribution.state_uncommitted_changes
    sync.status = 'success'

    sync.save()
    sync.contribution.save()
