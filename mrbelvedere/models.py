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
                slug = job_id,
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
    slug = models.SlugField()
    owner = models.CharField(max_length=255)
    url = models.URLField()
    username = models.CharField(max_length=255, null=True, blank=True)
    password = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return self.slug

    def call_api(self, subpath, data=None):
        """ Takes a subpath under the repository (ex: /releases) and returns the json data from the api """
        api_url = 'https://api.github.com/repos/%s/%s%s' % (self.owner, self.slug, subpath)
        # Use Github Authentication if available for the repo
        kwargs = {}
        if self.username and self.password:
            kwargs['auth'] = (self.username, self.password)

        if data:
            resp = requests.post(api_url, data=json.dumps(data), **kwargs)
        else:
            resp = requests.get(api_url, **kwargs)

        data = json.loads(resp.content)
        return data

    def get_latest_release(self, beta=None):
        if not beta:
            beta = False

        data = self.call_api('releases')    

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
        resp = self.call_api(self, '/hooks')
        existing = None
        for hook in resp:
            if hook['config']['url'].startswith(base_url):
                existing = hook
                break
        if existing:
            data = existing
            if 'push' not in data['events']:
                data['events'].append('push')
            if 'pull_request' not in data['events']:
                data['events'].append('pull_request')
            if 'pull_request_review_comment' not in data['events']:
                data['events'].append('pull_request_review_comment')
            
            return self.call_api('/hooks/%s/', data)

        self.call_api('/hooks/', data={
            'name': 'web',
            'config': {
                'url': base_url + '/mrbelvedere/githib-webhook',
            },
            events: [
                'push',
                'pull_request',
                'pull_request_review_comment',
            ],
            active: True,
        })


class Branch(models.Model):
    slug = models.SlugField()
    repository = models.ForeignKey(Repository)
    github_name = models.CharField(max_length=255)
    jenkins_name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.slug

class Job(models.Model):
    slug = models.SlugField()
    auth_token = models.CharField(max_length=255, null=True, blank=True)
    site = models.ForeignKey(JenkinsSite)
    # FIXME: re-enable field once logic is in place to populate repository from Jenkins data
    #repository = models.ForeignKey(Repository)

    def __unicode__(self):
        return self.slug

    def get_api(self, api=None):
        """ Get the jenkinsapi job object for this job """
        if not api:
            api = self.site.get_api()
            # NOTE: This will raise a KeyError if the job disappears from Jenkins
            return api[self.slug]
        

class RepositoryNewBranchJob(models.Model):
    repository = models.ForeignKey(Repository)
    job = models.ForeignKey(Job)
    prefix = models.CharField(max_length=128, null=True, blank=True)

    #def __unicode__(self):
    #    if self.repository and self.job:
    #        '%s -> %s' % (self.repository.slug, self.job.slug)

class BranchJobTrigger(models.Model): 
    branch = models.ForeignKey(Branch)
    job = models.ForeignKey(Job)
    active = models.BooleanField(default=True)
    last_trigger_date = models.DateTimeField(null=True, blank=True)

    #def __unicode__(self):
    #    return '%s -> %s' (self.branch.slug, self.job.slug)

    @django_rq.job
    def invoke(self, push):
        api = self.job.get_api()
        api.invoke(build_params={
            'branch': push.branch.slug,
            'email': push.github_user.email,
        })

class GithubUser(models.Model):
    slug = models.SlugField()
    name = models.CharField(max_length=255)
    email = models.EmailField()

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

from mrbelvedere.handlers import *
