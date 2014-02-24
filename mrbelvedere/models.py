from django.db import models
from django.template.defaultfilters import slugify
from jenkinsapi.jenkins import Jenkins
from xml.dom import minidom
import requests
import json
import django_rq

class JenkinsSite(models.Model):
    slug = models.SlugField()
    url = models.URLField(max_length=255)
    user = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
        
    def __unicode__(self):
        return self.slug

    def get_api(self):
        """ returns a jenkinsapi object to interact with the site """
        return Jenkins(self.url, self.user, self.password)

    def update_jobs(self):
        """ Creates or Updates Jobs by polling Jenkins Site API for current jobs.
            NOTE: This does not delete jobs.  The update is only to update the 
            authToken for the job if it was changed.
        """
        J = self.get_api()
        for job_id, job_info in J.items():
            auth_token = self.get_job_token(job_info)
            job = Job.objects.get_or_create(
                name = job_id,
                auth_token = auth_token,
                site=self,
            )[0]
            # If the job already existed, it may have an old auth_token
            if job.auth_token != auth_token:
                job.auth_token = auth_token
                job.save()

    def get_job_token(self, job_info):
        """ Accepts a jenkinsapi job object and returns the authToken from config """
        config = minidom.parseString(job_info.get_config())
        tokens = config.getElementsByTagName('authToken')
        if tokens:
            return tokens[0].firstChild.nodeValue

class Repository(models.Model):
    name = models.CharField(max_length=255)
    owner = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    username = models.CharField(max_length=255, null=True, blank=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    forks = models.ForeignKey('self', null=True, blank=True)

    def __unicode__(self):
        return '%s/%s' % (self.owner, self.name)

    def call_api(self, subpath, data=None, username=None, password=None):
        """ Takes a subpath under the repository (ex: /releases) and returns the json data from the api """
        api_url = 'https://api.github.com/repos/%s/%s%s' % (self.owner, self.name, subpath)
        # Use Github Authentication if available for the repo
        kwargs = {}
        if self.username and self.password:
            kwargs['auth'] = (self.username, self.password)

        if data:
            resp = requests.post(api_url, data=json.dumps(data), **kwargs)
        else:
            resp = requests.get(api_url, **kwargs)

        try:
            data = json.loads(resp.content)
            return data
        except:
            return resp.status_code

    def get_latest_release(self, beta=None):
        if not beta:
            beta = False

        data = self.call_api('/releases')

        for release in data:
            # Releases are returned in reverse chronological order.

            # If release is not of the prerelease status (production or beta) we are looking for, skip it
            if release['prerelease'] != beta:
                continue

            # If release does not have an install link in the body, skip it
            if release['body'].find('https://login.salesforce.com/packaging/installPackage.apexp') == -1:
                continue

            # If we got here, this is the release we're looking for
            return release

    def get_latest_release_name(self, beta=None):
        rel = self.get_latest_release(beta)
        if rel:
            return rel['name']

    def get_latest_release_tag(self, beta=None):
        rel = self.get_latest_release(beta)
        if rel:
            return rel['tag_name']

    def create_webhooks(self, base_url):
        resp = self.call_api('/hooks')
        target_urls = {
            'push': base_url + '/mrbelvedere/github/webhook/push/',
            'issue_comment': base_url + '/mrbelvedere/github/webhook/issue_comment/',
            'pull_request': base_url + '/mrbelvedere/github/webhook/pull_request/',
        }
        existing = {}

        for hook in resp:
            # Skip non-web hooks
            if hook['name'] != 'web':
                continue
            if hook['config']['url'] in target_urls.values():
                existing[hook['config']['url']] = hook

        hooks = [
            {
                'name': 'web',
                'config': {'url': target_urls['push']},
                'events': ['push'],
                'active': True,
            },
            {
                'name': 'web',
                'config': {'url': target_urls['issue_comment']},
                'events': ['issue_comment'],
                'active': True,
            },
            {
                'name': 'web',
                'config': {'url': target_urls['pull_request']},
                'events': ['pull_request'],
                'active': True,
            },
        ]

        created = 0
        updated = 0

        for hook in hooks:
            existing_hook = existing.get(hook['config']['url'], None)
            if existing_hook and existing_hook != hook:
                resp = self.call_api('/hooks/%s' % existing_hook['id'], hook)
                updated += 1
            else:
                resp = self.call_api('/hooks', hook)
                created += 1

        return 'Created %s hooks and updated %s hooks' % (created, updated)

    def can_write(self, username):
        """ Takes a github username and returns True if the user has write permissions to the repository in github """
        resp = self.call_api('/collaborators/%s' % username)
        if resp == 204:
            return True

class Branch(models.Model):
    name = models.CharField(max_length=255)
    repository = models.ForeignKey(Repository)
    github_name = models.CharField(max_length=255)
    jenkins_name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

class Job(models.Model):
    name = models.CharField(max_length=255)
    auth_token = models.CharField(max_length=255, null=True, blank=True)
    site = models.ForeignKey(JenkinsSite)
    # FIXME: re-enable field once logic is in place to populate repository from Jenkins data
    #repository = models.ForeignKey(Repository)

    def __unicode__(self):
        return self.name

    def get_api(self, api=None):
        """ Get the jenkinsapi job object for this job """
        if not api:
            api = self.site.get_api()
            # NOTE: This will raise a KeyError if the job disappears from Jenkins
            return api[self.name]
        

class RepositoryNewBranchJob(models.Model):
    repository = models.ForeignKey(Repository)
    job = models.ForeignKey(Job)
    prefix = models.CharField(max_length=128, null=True, blank=True)

    #def __unicode__(self):
    #    if self.repository and self.job:
    #        '%s -> %s' % (self.repository.name, self.job.name)

class BranchJobTrigger(models.Model): 
    branch = models.ForeignKey(Branch)
    job = models.ForeignKey(Job)
    active = models.BooleanField(default=True)
    last_trigger_date = models.DateTimeField(null=True, blank=True)

    #def __unicode__(self):
    #    return '%s -> %s' (self.branch.name, self.job.name)

    @django_rq.job
    def invoke(self, push):
        api = self.job.get_api()
        api.invoke(build_params={
            'branch': push.branch.name,
            'email': push.github_user.email,
        })

class GithubUser(models.Model):
    slug = models.SlugField()
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    def __unicode__(self):
        return self.slug

class Push(models.Model):
    slug = models.SlugField()
    message = models.TextField()
    branch = models.ForeignKey(Branch)
    github_user = models.ForeignKey(GithubUser)
    commit_url = models.URLField()
    
    def __unicode__(self):
        return self.slug

class PullRequest(models.Model):
    repository = models.ForeignKey(Repository)
    number = models.IntegerField()
    name = models.CharField(max_length=255)
    message = models.TextField(null=True, blank=True)
    source_branch = models.ForeignKey(Branch, related_name='pull_requests_source')
    target_branch = models.ForeignKey(Branch, related_name='pull_requests_target')
    approved = models.BooleanField(default=False)
    github_user = models.ForeignKey(GithubUser)
    base_sha = models.CharField(max_length=64)
    head_sha = models.CharField(max_length=64)
    last_build_head_sha = models.CharField(max_length=64, null=True, blank=True)
    last_build_base_sha = models.CharField(max_length=64, null=True, blank=True)
    state = models.CharField(max_length=32, default='open')

class PullRequestComment(models.Model):
    pull_request = models.ForeignKey(PullRequest)
    github_user = models.ForeignKey(GithubUser)
    message = models.TextField()

class RepositoryPullRequestJob(models.Model):
    repository = models.ForeignKey(Repository)
    job = models.ForeignKey(Job)
    forked = models.BooleanField(default=True)
    internal = models.BooleanField(default=False)
    moderated = models.BooleanField(default=True)
    repo_admins = models.BooleanField(default=True)
    admins = models.ManyToManyField(GithubUser, null=True, blank=True)

    def is_admin(self, username):
        if not self.moderated:
            return True
        is_admin = self.admins.filter(slug=username).count()
        if is_admin:
            return True
        if self.repo_admins and self.repository.can_write(username):
            return True
        return False
        
    @django_rq.job
    def invoke(self, pull_request):
        source_repo = pull_request.source_branch.repository
        target_repo = pull_request.target_branch.repository
        if source_repo != target_repo:
            if not self.forked:
                return
        else:
            if not self.internal:
                return

        api = self.job.get_api()
        repo_url = pull_request.source_branch.repository.url.replace('git://github.com/','git@github.com:')
        params={
            'repository': repo_url,
            'branch': pull_request.source_branch.name,
        }
        if pull_request.github_user.email:
            params['email'] = pull_request.github_user.email
            
        result = api.invoke(build_params=params)
        build_url = result.get_build().baseurl

        # build_url seems to return the last build.  Rather than blocking until this job starts, 
        # we'll just presume its number is one higher than the current
        parts = build_url.split('/')
        build_url = '/'.join(parts[:-1]) + '/' + str(int(parts[-1])+1)

        # Post a comment on the pull request with link to build

        # commented code because we don't need write access to set status but may at some point in the future for other reasons
        #can_write = source_repo.can_write(target_repo.username)
        body = 'OK, build is started.  You can view status at %s.  If you get a 404, please try again later as the build might be queued.' % build_url
        #if can_write:
        body = '%s  I will update the build status on the pull request when the build is done' % body
        #else:
        #    body = '%s  @%s, If you add %s as a collaborator on your fork I can set the build status for you.' % (body, pull_request.github_user.slug, target_repo.username)

        comment = pull_request.repository.call_api('/issues/%s/comments' % pull_request.number, data={'body': body})

        # Get the current sha from head and base to record last build
        pr = pull_request.repository.call_api('/pulls/%s' % pull_request.number)
        pull_request.last_build_head_sha = pr['head']['sha']
        pull_request.last_build_base_sha = pr['base']['sha']
        pull_request.save()

        return result

from mrbelvedere.handlers import *
