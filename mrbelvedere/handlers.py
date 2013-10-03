from django.db.models.signals import post_save
from django.dispatch import receiver
from mrbelvedere.models import Branch, Push, BranchJobTrigger

@receiver(post_save, sender=Branch)
def create_new_branch_job_triggers(sender, **kwargs):
    if not kwargs['created']:
        # Only run on create
        return

    branch = kwargs['instance']
    for branchjob in branch.repository.repositorynewbranchjob_set.all():
        trigger = BranchJobTrigger(
            branch = branch,
            job = branchjob.job,
        )
        trigger.save()

@receiver(post_save, sender=Push)
def trigger_jenkins_jobs_on_push(sender, **kwargs):
    if not kwargs['created']:
        # Only run on create
        return
       
    push = kwargs['instance']
    for trigger in push.branch.branchjobtrigger_set.all():
        trigger.invoke(push)
