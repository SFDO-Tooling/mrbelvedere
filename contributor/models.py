import hashlib
import time
import traceback
from datetime import datetime
from django.db import models
from django.contrib.auth.models import User
from mpinstaller.github import github_api
from mpinstaller.github import SalesforcePackageToGithub
from mpinstaller.handlers import install_package_version
from mpinstaller.installer import version_install_map
from mpinstaller.installer import install_map_to_json
from mpinstaller.mdapi import ApiRetrievePackaged
from mpinstaller.mdapi import ApiRetrieveInstalledPackages
from mpinstaller.models import PackageInstallation
from mpinstaller.models import PackageInstallationSession
from mpinstaller.models import PackageInstallationStep
from mpinstaller.models import PackageVersion
from contributor.exceptions import DefaultBranchSyncFailed
from tinymce.models import HTMLField

SYNC_STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('in_progress', 'In Progress'),
    ('success', 'Successful'),
    ('fail', 'Failed'),
)

class Contributor(models.Model):
    user = models.ForeignKey(User, related_name='contributors')

    def __unicode__(self):
        return self.user.username

class Contribution(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    package_version = models.ForeignKey(PackageVersion, related_name='contributions')
    contributor = models.ForeignKey(Contributor, related_name='contributions')
    sf_oauth = models.TextField(null=True, blank=True)
    github_issue = models.IntegerField(null=True, blank=True)
    fork_branch = models.CharField(max_length=255, null=True, blank=True)
    fork_merge_branch = models.CharField(max_length=255, null=True, blank=True)
    main_branch = models.CharField(max_length=255, null=True, blank=True)
    fork_pull = models.IntegerField(null=True, blank=True)
    main_pull = models.IntegerField(null=True, blank=True)
    default_branch_synced = models.BooleanField(default=False)
    state_behind_main = models.BooleanField(default=False)
    state_undeployed_commit = models.BooleanField(default=False)
    state_uncommitted_changes = models.BooleanField(default=False)
    last_deployed_date = models.DateTimeField(null=True, blank=True)
    last_deployment_installation = models.ForeignKey('mpinstaller.PackageInstallation', related_name='contributions', null=True, blank=True)
    last_deployed_commit = models.CharField(max_length=255, null=True, blank=True)
    last_retrieve_checksum = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return '%s: %s' % (self.package_version.package.namespace, self.title)

    def decode_sf_oauth(self):
        if self.sf_oauth:
            return json.loads(self.sf_oauth)

    def can_view(self, user):
        # Only the contributor or a staff user can view
        if self.contributor.user != user and not user.is_staff:
            return False
        return True
    
    def can_edit(self, user):
        # For now, view and edit are the same permission, replace this later to implement different acl logic
        return self.can_view(user)

    def can_review(self, user):
        return False

    def github_token(self):
        github_auth = self.contributor.user.social_auth.filter(provider = 'github')
        if github_auth.count():
            github_auth = github_auth[0]
            github_auth.refresh_token()
        if github_auth:
            return github_auth.tokens['access_token']

    def github_api(self, path, data=None, fork=None, as_contributor=None):
        if fork:
            owner = self.contributor.user.username
            username = self.github_token()
            password = ''
        else:
            owner = self.get_main_repo_owner()
            if as_contributor:
                username = self.github_token()
                password = ''
            else:
                username = self.package_version.github_username
                password = self.package_version.github_password

        return github_api(
            owner = owner,
            repo = self.get_main_repo_name(),
            subpath = path,
            data = data,
            username = username,
            password = password,
        )

    def get_main_repo_owner(self):
        return self.package_version.repo_url.split('/')[3]

    def get_main_repo_name(self):
        return self.package_version.repo_url.split('/')[4]

    def get_fork(self):
        fork = self.github_api('', fork=True)
        if 'message' in fork:
            if fork['message'] != 'Not Found':
                return fork
        else:
            return fork

        # If no fork was found, create it
        fork = self.github_api('/forks', data={}, as_contributor=True)

        # If there was any message in the response, we hit an error... return it
        if 'message' in fork:
            return fork

        # Since fork creation happens async, wait for up to 5 minutes per GitHub
        timeout = time.time() + 60*5
        while True:
            time.sleep(3)
            fork = self.github_api('', fork=True)

            if 'message' in fork:
                if fork['message'] != 'Not Found':
                    # Anything other than Not Found will not be resolved with time, give up now
                    break
            else:
                return fork

            if time.time() > timeout:
                # We reached the timeout, give up and return whatever response we got from GitHub
                break

            print 'Timeout in %s seconds' % (timeout - time.time())
             
        return fork

    def get_default_branch(self, fork=None):
        repo = self.github_api('', fork=fork)
        branch = self.github_api('/git/refs/heads/%s' % repo['default_branch'], fork=fork)
        return branch

    def get_fork_branch(self):
        if not self.fork_branch:
            return

        if not self.default_branch_synced:
            self.update_default_branch()

        branch = self.github_api('/git/refs/heads/%s' % self.fork_branch, fork=True)
        if 'message' in branch and branch['message'] == 'Not Found':

            # FIXME: Verify that fork default branch is not behind main default branch

            repo = self.github_api('', fork=True)
            default_branch = self.get_default_branch(fork=True)

            data = {
                'ref': 'refs/heads/%s' % self.fork_branch,
                'sha': default_branch['object']['sha'],
            }
            branch = self.github_api('/git/refs', data=data, fork=True)

        return branch        

    def get_main_branch(self):
        if not self.main_branch:
            return

        branch = self.github_api('/git/refs/heads/%s' % self.main_branch, main=True)
        if 'message' in branch and branch['message'] == 'Not Found':
        
            repo = self.github_api('')
            default_branch = self.get_default_branch()

            data = {
                'ref': 'refs/heads/%s' % self.main_branch,
                'sha': default_branch['object']['sha'],
            }
            branch = self.github_api('/git/refs', data=data)

        return branch

    def get_fork_pull(self):
        # FIXME: Needs implementation
        pass

    def get_main_pull(self):
        # FIXME: Needs implementation
        pass

    def update_default_branch(self):
        """ Updates the fork's default branch with the main repository's default branch's HEAD """

        if self.default_branch_synced:
            return True

        default_branch = self.github_api('')['default_branch']
        main_sha = self.github_api('/git/refs/heads/%s' % default_branch)['object']['sha']
        fork_sha = self.github_api('/git/refs/heads/%s' % default_branch, fork=True)['object']['sha']
        if main_sha != fork_sha:
            res = self.github_api('/merges', data={"base": default_branch, "head": main_sha}, fork=True)
            if res == 204 or 'messages' not in res:
                self.default_branch_synced = True
                self.save()
            else:
                raise DefaultBranchException('Failed to merge commit "%s" from main repository default branch "%s" to fork' % (main_sha, default_branch), res)
        return True

    def get_issue(self):
        if not self.github_issue:
            if not self.title or not self.body:
                return

        issue = self.github_api('/issues/%s' % self.github_issue)
        if 'message' in issue and issue['message'] == 'Not Found':
            # The issue was not found, create it
            data = {
                'title': self.title,
                'body': self.body,
                # FIXME: We can't set an assignee to the contributor as they need write access to the repo to receive issue assignments.  We need a reviewer for this
                #'assignee': self.contributor.user.username,
            }
            issue = self.github_api('/issues', data=data)
        
        return issue

    def search_issues(self, q):
        return self.github_api('/search/issues?q=%s' % quote(q))

    def has_user_commit(self):
        count = self.syncs.filter(status = 'success', message__isnull = False).count()
        return count > 0

    def check_sync_state(self, sync=None):
        # Check if behind_main
        # FIXME: Needs implementation
            
        fork = self.get_fork()
        branch = self.get_fork_branch()

        # Check if undeployed_commit
        if sync:
            sync.log += '--- * Checking for undeployed commit from Github\n'
            sync.save()
        if not self.last_deployed_commit:
            # If we've never deployed a commit, set True
            self.state_undeployed_commit = True
        else:
            if branch['object']['sha'] != self.last_deployed_commit:
                # If we've not deployed the head commit, set True
                self.state_undeployed_commit = True
            else:
                # If we've already deployed the head commit, set False
                self.state_undeployed_commit = False

        # Check if uncommitted_changes
        if sync:
            sync.log += '--- * Checking for unsaved changes in the Salesforce DE org\n'
            sync.save()
        if not self.last_retrieve_checksum:
            # If we've never done a retrieve, set False since we assume we start from a clean org
            self.state_uncommitted_changes = False
        else:
            # Attempt to retrieve from the org
            org_metadata = self.retrieve_packaged()
            if sync:
                sync.log += '--- * Retrieving packaged metadata from Salesforce DE org\n'
                sync.save()
            org_checksum = self.calculate_retrieve_checksum(org_metadata)

            if org_checksum != self.last_retrieve_checksum:
                self.state_uncommitted_changes = True
            else:
                self.state_uncommitted_changes = False

        # NOTE: We don't save here so that the caller can choose when to retrigger handlers

    def retrieve_packaged(self):
        oauth = self.decode_sf_oauth()
        api = ApiRetrievePackaged(oauth, self.package_version.package_name)
        return api()
            
    def calculate_retrieve_checksum(self, zipf):
        """ Returns an md5 sum of the concatenated CRC's from each file in a python zipfile """
        aggregate_crc = []
        for name in zipf.namelist():
            aggregate_crc.append(str(zipf.getinfo(name).CRC))

        return hashlib.md5(''.join(aggregate_crc)).hexdigest()

    def sync(self):
        try:
            sync = ContributionSync(
                contribution = self,
                pre_state_behind_main = self.state_behind_main,
                pre_state_undeployed_commit = self.state_undeployed_commit,
                pre_state_uncommitted_changes = self.state_uncommitted_changes,
                log = '---- Checking current sync state\n',
                status = 'in_progress',   
            )
            sync.save()

            # Update current sync state
            state_before = (self.state_behind_main, self.state_undeployed_commit, self.state_uncommitted_changes)
            self.check_sync_state(sync)
  
            sync.log += 'DONE\n' 
            sync.save()
            sync.pre_state_behind_main = self.state_behind_main
            sync.pre_state_undeployed_commit = self.state_undeployed_commit
            sync.pre_state_uncommitted_changes = self.state_uncommitted_changes
            sync.save()
    
            changed = False
    
            first_sync = False
            if not self.last_retrieve_checksum:
                first_sync = True
                
            if self.state_uncommitted_changes:
                sync.log += '----- State: Uncommitted Changes = True\n'
                sync.save()
    
                if self.state_undeployed_commit:
                    # Save org metadata to new branch and prepare 3 way merge
    
                    sync.log += '--- Undeployed Commit and Uncommitted Changes - 3 way merge\n'
                    sync.save()
    
                    # Retrieve org metadata
                    sync.log += 'Retrieving org metadata...\n'
                    sync.save()
    
                    org_metadata = self.retrieve_packaged()
    
                    sync.log += 'DONE\n'
                    sync.save()
    
                    # Create the merge branch from the last deployed commit
                    self.merge_branch = '%s-devorg-%s' % (self.fork_branch, self.last_deployed_commit),
    
                    sync.log += 'Creating merge branch %s...\n' % self.merge_branch
                    sync.save()
    
                    data = {
                        'ref': 'refs/heads/%s' % self.merge_branch,
                        'sha': self.last_deployed_commit,
                    }
                    branch = self.github_api('/git/refs', data=data, fork=True)
    
                    sync.log += 'DONE, sha = %s\n' % branch['object']['sha']
                    sync.save()
    
                    # Commit retrieved metadata to the merge branch
                    sync.log += 'Commit from org to merge branch...\n'
                    sync.save()
    
                    commit = self.commit_from_org(message='Automated commit to save DE org changes before deployment from branch', branch=self.merge_branch)
    
                    sync.log += 'DONE, sha = %s\n' % commit['sha']
                    sync.save()
    
                    changed = True

                    # FIXME: Merge the branch
                else:
                    # If there are no undeployed changes, do nothing.  Commits are 
                    # only made manually by the user when they provide a commit message
                    pass
    
            if self.state_undeployed_commit:
                # Deploy the commit to the DE org
                sync.log += '----- State: Undeployed Commit = True\n'
                sync.log += 'Deploying HEAD commit to org...\n'
                sync.save()
    
                installation = self.deploy_commit_to_org(sync)
    
                if installation:
                    if installation.status == 'Failed':
                        sync.log += 'FAILED, Installation #%s failed\n' % installation.id
                        sync.log += installation.log
                        sync.save()
                        for step in installation.steps.filter(status='Failed'):
                            sync.log += step.log
                            sync.save()
                        sync.status = 'failed'
                    else:
                        sync.log += 'DONE, Installed with PackageInstallation #%s\n' % installation.id
                        sync.save()

                    sync.new_installation = installation
                    sync.save()
    
                    # Only mark changed if we started a new installation
                    changed = True
    
            if self.state_behind_main:
                # FIXME: Implement handling
                pass
    
            if first_sync and self.last_deployed_commit and sync.status != 'failed':
                sync.log += '----- Initial Deployment: Commit from org\n'
                sync.log += 'Retrieving from org and committing\n'
                sync.save()
    
                commit = self.commit_from_org(message='Initial commit after first sync')
    
                sync.log += 'DONE, sha = %s\n' % commit['sha']
                sync.new_commit = commit['sha']
                sync.save()    
     
   
            sync.log += '----- Checking post sync state...\n' 
            sync.save()
    
            # If state changed at all, set changed to True
            after_state = (self.state_behind_main, self.state_undeployed_commit, self.state_uncommitted_changes)
            if state_before != after_state:
                changed = True
    
            self.check_sync_state(sync)
    
            sync.log += 'DONE\n'
            sync.save()
            sync.post_state_behind_main = self.state_behind_main
            sync.post_state_undeployed_commit = self.state_undeployed_commit
            sync.post_state_uncommitted_changes = self.state_uncommitted_changes
            if sync.status != 'failed':
                sync.status = 'success'
            sync.save()
    
            return changed

        except Exception, e:
            sync.log += '----------------------------\n'
            sync.log += 'FAILED: %s\n' % e
            sync.log += '----------------------------\n'
            sync.log += traceback.format_exc()
            sync.status = 'failed'
            sync.save()

            # Return a normal result since the job did complete
            return changed

    def deploy_commit_to_org(self, commit=None, sync=None):
        if not self.sf_oauth:
            if sync:
                sync.log += 'FAILED: No Saleforce Org credentials available to sync with DE org\n'
                sync.status = 'failed'
                sync.save()
            return 

        # If there is currently an installation running, return None
        if self.last_deployment_installation and self.last_deployment_installation.status in ('Pending','In Progress'):
            if sync:
                sync.log += 'FAILED: Another installation is already in progress for this contribution.  Please try again later\n'
                sync.status = 'failed'
                sync.save()
            return

        version = self.package_version
        oauth = self.decode_sf_oauth()

        if commit:
            git_ref = commit
        else:
            git_ref = self.fork_branch

        fork = self.contributor.user.username

        # Get installed packages in org
        api = ApiRetrieveInstalledPackages(oauth)
        if sync:
            sync.log += '--- Getting list of installed packages in org\n'
            sync.save()
        installed = api()
        if sync:
            sync.log += 'DONE'
            sync.save()
       
        # Store the access token from the api call if it changed 
        if api.oauth != oauth:
            self.sf_oauth = json.dumps(api.oauth)
        else:
            installed = {}

        # With GitHub installations, we don't run conditions since we dynamically construct the install map
        metadata = {}

        # Build the install map
        install_map = version_install_map(version, installed, metadata, git_ref, fork)

        if sync:
            sync.log += '--- Configuring installation steps\n'
            sync.save()

        # Build the Installation object
        installation_obj = PackageInstallation(
            package = version.package,
            version = version,
            git_ref = git_ref,
            fork = fork,
            org_id = oauth['org_id'],
            org_type = oauth['org_type'],
            instance_url = oauth['instance_url'],
            status = 'Pending',
            username = oauth['username'],
            install_map = install_map_to_json(install_map),
        )
        installation_obj.save()

        # Create a PackageInstallationSession so we can reuse the same install method from mpinstaller
        session_obj = PackageInstallationSession(
            installation = installation_obj,
            oauth = json.dumps(oauth),
            org_packages = json.dumps(installed),
            metadata = json.dumps(metadata)
        )
        session_obj.save()

        order = 0

        # Create the PackageInstallationStep objects
        for step in install_map:
            step_obj = PackageInstallationStep(
                installation = installation_obj,
                package = step['version'].package,
                version = step['version'],
                previous_version = step['installed'],
                action = step['action'],
                status = 'Pending',
                order = order,
            )
            order += 1
            if step_obj.action == 'skip':
                step_obj.status = 'Succeeded'
            else:
                if sync:
                    sync.log += '--- * %s: %s\n' % (step_obj.version, step_obj.action)
                    sync.save()
            step_obj.save()

        if sync:
            sync.log += 'DONE\n\n'
            sync.log += '--- Starting installation #%s\n' % installation_obj.id
            sync.log += '--- * NOTE: This can take anywhere from 5-15 minutes to complete\n'
            sync.log += '--- * <a href="/mpinstaller/installations/%s" target="_blank">View installation status in separate tab</a>\n'
            sync.save()

        # Run the installer synchronously since we should already be inside a background process
        install_package_version(installation_obj.id)

        if sync:
            sync.log += 'DONE\n\n'
            sync.save()

        # Record the deployment on the Contribution if successful
        self.last_deployment_installation = installation_obj
        self.last_deployment_date = datetime.now()
        if installation_obj.status != 'Failed':
            if commit:
                self.last_deployed_commit = commit
            else:
                branch = self.get_fork_branch()
                self.last_deployed_commit = branch['object']['sha']

        return installation_obj

    def commit_from_org(self, message, branch=None):
        if not branch:
            branch = self.fork_branch

        sf_auth = self.decode_sf_oauth()
        github_token = self.github_token()
        github_auth = self.contributor.user.social_auth.filter(provider = 'github')
        if github_auth.count():
            github_auth = github_auth[0]
            github_auth.refresh_token()

        if not sf_auth or not github_auth:
            return 

        push = SalesforcePackageToGithub(
            github_owner = self.contributor.user.username,
            github_repo = self.get_main_repo_name(),
            package_name = self.package_version.package_name,
            username = github_token,
            password = None,
            branch = branch,
        )

        commit = push(
            oauth = sf_auth,
            message = message,
            subpath = self.package_version.subfolder,
        )

        # Set the md5sum of the retrieved metadata
        self.last_retrieve_checksum = self.calculate_retrieve_checksum(push.org_metadata)

        # Set last deployed commit to the newly created commit since we just retrieved from the org
        if commit:
            self.last_deployed_commit = commit['sha']
            self.last_deployed_date = datetime.now()

        return commit

class ContributionSync(models.Model):
    contribution = models.ForeignKey(Contribution, related_name="syncs")
    status = models.CharField(max_length=32, choices=SYNC_STATUS_CHOICES, default="pending")
    log = models.TextField(null=True, blank=True, default='')
    message = models.TextField(null=True, blank=True)
    new_commit = models.CharField(max_length=64, null=True, blank=True)
    new_installation = models.ForeignKey('mpinstaller.PackageInstallation', null=True, blank=True, related_name='contribution_syncs')
    pre_state_behind_main = models.BooleanField()
    pre_state_undeployed_commit = models.BooleanField()
    pre_state_uncommitted_changes = models.BooleanField()
    post_state_behind_main = models.BooleanField()
    post_state_undeployed_commit = models.BooleanField()
    post_state_uncommitted_changes = models.BooleanField()
    date_started = models.DateTimeField(auto_now_add = True)
    date_modified = models.DateTimeField(auto_now = True)

from contributor.handlers import *
