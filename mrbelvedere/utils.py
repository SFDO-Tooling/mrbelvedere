import json
from mrbelvedere.models import Repository, Branch, Push, GithubUser

class GithubWebhookParser(object):
    """ Receives a Github payload json string and splits into attributes.
        Special attributes branch, repository, github_user, and push fetch
        or create the coresponding objects from mrbelvedere.models
    """

    def __init__(self, payload):
        # Parse the payload json
        payload = json.loads(payload)

        # Set payload keys as attributes
        self.repository = payload.get('repository')
        self.before = payload.get('before')
        self.after = payload.get('after')
        self.compare = payload.get('compare')
        self.pusher = payload.get('pusher')
        self.deleted = payload.get('deleted')
        self.commits = payload.get('commits')
        self.head_commit = payload.get('head_commit')
        self.forced = payload.get('forced')
        self.created = payload.get('created')
        self.ref = payload.get('ref')

    @property
    def repository_obj(self):
        return Repository.objects.get_or_create(
            slug = self.repository['name'],
            url = self.repository['url'],
        )[0] 
   
    @property
    def branch_obj(self):
        return Branch.objects.get_or_create(
            slug = self.ref.replace('refs/heads/', ''),
            repository = self.repository_obj,
            github_name = self.ref,
            jenkins_name = self.ref.replace('refs/heads', 'origin'),
        )[0]

    @property
    def github_user_obj(self):
        committer = self.head_commit['committer']
        return GithubUser.objects.get_or_create(
            slug = committer['username'],
            name = committer['name'],
            email = committer['email'],
        )[0]

    @property
    def push_obj(self):
        commit = self.head_commit
        return Push.objects.get_or_create(
            slug = commit['id'],
            message = commit['message'],
            branch = self.branch_obj,
            github_user = self.github_user_obj,
            commit_url = commit['url'],
        )[0]
