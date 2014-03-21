from django.db.models.signals import post_save
from django.dispatch import receiver
from time import sleep
import django_rq
import selenium
from selenium import webdriver
from django.db import transaction
from mrbelvedere.models import Branch, Push, BranchJobTrigger, PullRequest, PullRequestComment, PackageBuilderBuild

@receiver(post_save, sender=Branch)
def create_new_branch_job_triggers(sender, **kwargs):
    if not kwargs['created']:
        # Only run on create
        return

    branch = kwargs['instance']
    for branchjob in branch.repository.repositorynewbranchjob_set.all():
        if branchjob.prefix and branch.github_name.startswith(branchjob.prefix):
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

@receiver(post_save, sender=PullRequest)
def moderate_pull_request_build(sender, **kwargs):
    pull_request = kwargs['instance']

    # Build a query to look for RepositoryPullRequestJob objects which require modification for the pull request 
    forked = pull_request.source_branch.repository != pull_request.target_branch.repository
    query = {}
    if forked:
        query['forked'] = True
    else:
        query['internal'] = True
    triggers = pull_request.repository.repositorypullrequestjob_set.filter(**query)

    # Do nothing if we have no triggers that apply to this pull request
    if not triggers.count():
        return

    # If we have already built the head, do nothing
    if pull_request.last_build_head_sha == pull_request.head_sha:
        return

    # Skip closed pull requests
    if pull_request.state == 'closed':
        return

    # Validate the branch name format
    valid_branch = True
    branch_comment = None
    if not pull_request.source_branch.name.startswith('feature/'):
        valid_branch = False

        branch_comment = 'Your branch does not meet the feature branch naming requirements.  The name must use the format feature/NNN-description-of-feature where NNN is a valid GitHub issue number from the main repository.  Please rename your branch and submit a new pull request.'

    # Attempt to parse the integer issue number from the branch name, fail with comment if it can't be parsed
    if valid_branch:
        issue_number = pull_request.source_branch.name.replace('feature/','').split('-')[0]
        try:
            int(issue_number)
        except:
            valid_branch = False
            branch_comment = 'Your branch does not meet the feature branch naming requirements.  I was unable to parse an issue number from the branch name.  The format should be feature/NNN-description-of-feature where NNN is the issue number.  Please rename your branch and submit a new pull request.'
   
    if valid_branch: 
        issue = pull_request.repository.call_api('/issues/%s' % issue_number)
        if issue == 404:
            valid_branch = False
            branch_comment = 'Your branch name specifies an issue number of %s which does not exist in the main repository.  Please rename the branch and open a new pull request.' % issue_number

    # If the branch name was invalid, close the pull request as a new one will need to be submitted from the renamed branch.
    if not valid_branch:
        # Close the pull request
        pull_request.repository.call_api('/pulls/%s' % pull_request.number, data={'state': 'closed'})
        # Then add comment (done after close to prevent double comment when PullRequestComment webhook calls back)
        pull_request.repository.call_api('/issues/%s/comments' % pull_request.number, data={'body': branch_comment})
        return
        
    # code below commented out since we don't need write access to set commit status
    # commit status is set on the target repo, not the source repo

    # If the target repo user does not have access to the source repo, request it
    #bot_username = pull_request.repository.username
    #req_username = pull_request.github_user.slug
    #if not pull_request.source_branch.repository.can_write(username):
    #    pull_request.repository.call_api('/issues/%s/comments' % pull_request.number, data={
    #        'body': "@%s I don't have access to the source repository.  Please add %s as a collaborator on the repository so I can set the build status on your pull request" % (bot_username, req_username),
    #    })
    #    # Don't return as we don't want this to block anything.  It's a nice to have but not a requirement

    # If head is behind base, comment that this needs to be resolved before a build
    compare = pull_request.repository.call_api('/compare/%s...%s' % (pull_request.base_sha, pull_request.head_sha))
    if compare['behind_by']:
        # Create comment requesting head be updated to be in sync with base
        pull_request.repository.call_api('/issues/%s/comments' % pull_request.number, data={
            'body': 'The branch requesting merge is currently behind the target branch by %s commits.  Please merge the commits so your branch is not behind the target branch.' % compare['behind_by'],
        })
        return

    # If the request is not approved, post a comment requesting approval
    if not pull_request.approved:
        # Create commment requesting approval
        comment = pull_request.repository.call_api('/issues/%s/comments' % pull_request.number, data={
            'body': 'Can an admin approve this request for build?',
        })
        return
    
    # If approved and build is needed, trigger builds
    for trigger in triggers:
        trigger.invoke(pull_request)

@receiver(post_save, sender=PullRequestComment)
def check_for_build_approval(sender, **kwargs):
    comment = kwargs['instance']

    if comment.message.find('**mrbelvedere: approved**') != -1:
        is_admin = False
    
        # Build a query to look for RepositoryPullRequestJob objects which require modification for the pull request 
        forked = comment.pull_request.source_branch.repository != comment.pull_request.target_branch.repository
        query = {'moderated': True}
        if forked:
            query['forked'] = True
        else:
            query['internal'] = True
 
        # NOTE: If you are an admin on any matching trigger, you are an admin on all matching triggers 
        for trigger in comment.pull_request.repository.repositorypullrequestjob_set.filter(**query):
            if trigger.is_admin(comment.github_user.slug):
                is_admin = True 
        if not is_admin:
            comment = pull_request.repository.call_api('/issues/%s/comments' % pull_request.number, data={
                'body': 'Ignoring approval from non-admin user %s' % comment.github_user.slug,
            })
            return

        if comment.pull_request.approved == False:
            comment.pull_request.approved = True
            comment.pull_request.save()

@receiver(post_save, sender=PackageBuilderBuild)
def queue_build_package(sender, **kwargs):
    # Only run when the build object is created
    if not kwargs.get('created', False):
        return
    build = kwargs['instance']

    build.status = 'Queued'
    build.message = 'Added to background job queue'
    build.save()
    
    build_package.delay(build)
    
@django_rq.job('default', timeout=1800)
def build_package(build):
    """ Builds a managed package by calling SauceLabs via Selenium to click the Upload button """ 
    # Update Status
    build.status = 'Starting'
    build.message = 'Starting browser at SauceLabs'
    build.save()

    driver = build.builder.org.saucelabs_connect()

    # Load the packages list page
    driver.get('%s/0A2' % build.builder.org.instance_url)

    # Update Status
    build.status = 'Starting'
    build.message = 'Loaded package listing page'
    build.save()

    # Click the link to the package
    driver.find_element_by_xpath("//th[contains(@class,'dataCell')]/a[text()='Cumulus']").click()

    # Update Status
    build.status = 'Starting'
    build.message = 'Loaded package page'
    build.save()

    # Click the Upload button to open the upload form
    driver.find_element_by_xpath("//input[@class='btn' and @value='Upload']").click()

    # Update Status
    build.status = 'Starting'
    build.message = 'Loaded Upload form'
    build.save()

    # Update Status
    build.status = 'Loaded Upload Form'
    build.save()

    # Populate and submit the upload form to create a beta managed package
    name_input = driver.find_element_by_id('ExportPackagePage:UploadPackageForm:PackageDetailsPageBlock:PackageDetailsBlockSection:VersionInfoSectionItem:VersionText')
    name_input.clear()
    name_input.send_keys(build.name)
    driver.find_element_by_id('ExportPackagePage:UploadPackageForm:PackageDetailsPageBlock:PackageDetailsPageBlockButtons:bottom:upload').click()

    # Update Status
    build.status = 'Uploading'
    build.message = 'Upload Submitted'
    build.save()

    # Monitor the package upload progress
    while True:
        try:
            status_message = driver.find_element_by_css_selector('.messageText').text
        except selenium.common.exceptions.StaleElementReferenceException:
            # These come up, possibly if you catch the page in the middle of updating the text via javascript
            sleep(1)
            continue
        if status_message.startswith('Upload Complete'):
            # Update Status
            build.status = 'Complete'
            build.message = status_message

            # Get the version number and install url
            version = driver.find_element_by_xpath("//th[text()='Version Number']/following-sibling::td/span").text
            install_url = driver.find_element_by_xpath("//a[contains(@name, ':pkgInstallUrl')]").get_attribute('href')
        
            build.version = version
            build.install_url = install_url
            build.save()

            break

        if status_message.startswith('Upload Failed'):
            build.status = 'Failed'
            build.message = status_message
            build.save()
            break 

        # Update Status
        build.status = 'Uploading'
        build.message = status_message
        build.save()

        sleep(1)

    build.save()

    driver.quit()
