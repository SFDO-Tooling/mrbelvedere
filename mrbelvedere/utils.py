import json
from mrbelvedere.models import Repository, Branch, Push, GithubUser, PullRequest, PullRequestComment

class GithubPushLoader(object):
    """ Receives a Github push payload json string and splits into attributes.
        Special attributes branch, repository, github_user, and push fetch
        or create the coresponding objects from mrbelvedere.models
    """

    def __init__(self, payload):
        # Parse the payload json
        payload = json.loads(payload)

        # Set payload keys as attributes
        self.repository = payload.get('repository', None)
        self.before = payload.get('before', None)
        self.after = payload.get('after', None)
        self.compare = payload.get('compare', None)
        self.pusher = payload.get('pusher', None)
        self.deleted = payload.get('deleted', None)
        self.commits = payload.get('commits', None)
        self.head_commit = payload.get('head_commit', None)
        self.forced = payload.get('forced', None)
        self.created = payload.get('created', None)
        self.ref = payload.get('ref', None)

    @property
    def repository_obj(self):
        return Repository.objects.get_or_create(
            name = self.repository['name'],
            owner = self.repository['owner']['name'],
            url = self.repository['git_url'],
        )[0] 
   
    @property
    def branch_obj(self):
        jenkins_name = self.ref.replace('ref/heads','origin')
        jenkins_name = jenkins_name.replace('refs/tags','origin/tags')
        return Branch.objects.get_or_create(
            name = self.ref.replace('refs/heads/', ''),
            repository = self.repository_obj,
            github_name = self.ref,
            jenkins_name = jenkins_name,
        )[0]

    @property
    def github_user_obj(self):
        committer = self.head_commit['committer']
        try:
            user = GithubUser.objects.get(slug = committer['username'])
            user.name = committer['name']
            user.email = committer['email']
        except GithubUser.DoesNotExist:
            user = GithubUser(
                slug = committer['username'],
                name = committer['name'],
                email = committer['email'],
            )
        user.save()
        return user

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

class GithubPullRequestLoader(object):
        
    def __init__(self, payload):
        payload = json.loads(payload)

        self.number = payload['pull_request']['number']
        self.title = payload['pull_request']['title']
        self.body = payload['pull_request']['body']
        self.username = payload['sender']['login']

        self.target_branch = payload['pull_request']['base']
        self.target_repository = self.target_branch['repo']
        self.source_branch = payload['pull_request']['head']
        self.source_repository = self.source_branch['repo']
    
    @property
    def repository_obj(self):
        return Repository.objects.get_or_create(
            name = self.target_repository['name'],
            owner = self.target_repository['owner']['login'],
            url = self.target_repository['git_url'],
        )[0]

    @property
    def source_repository_obj(self):
        return Repository.objects.get_or_create(
            name = self.source_repository['name'],
            owner = self.source_repository['owner']['login'],
            url = self.source_repository['git_url'],
        )[0]

    def get_branch_obj(self, branch, repository):
        name = branch['ref'].replace('refs/heads/', '')
        jenkins_name = branch['ref'].replace('ref/heads','origin')
        jenkins_name = jenkins_name.replace('refs/tags','origin/tags')
        return Branch.objects.get_or_create(
            name = name,
            repository = repository,
            github_name = branch['ref'],
            jenkins_name = jenkins_name,
        )[0]

    @property
    def source_branch_obj(self):
        return self.get_branch_obj(self.source_branch, self.source_repository_obj)

    @property
    def target_branch_obj(self):
        return self.get_branch_obj(self.target_branch, self.repository_obj)

    @property
    def github_user_obj(self):
        return GithubUser.objects.get_or_create(slug=self.username)[0]

    @property
    def pull_request_obj(self):
        repo = self.repository_obj

        try:
            pull = PullRequest.objects.get(repository=repo, number=self.number)
            pull.head_sha = self.source_branch['sha']
            pull.base_sha = self.target_branch['sha']
            pull.save()
        except PullRequest.DoesNotExist:
            pull = PullRequest(
                repository = repo,
                number = self.number,
                name = self.title,
                message = self.body,
                source_branch = self.source_branch_obj,
                target_branch = self.target_branch_obj,
                github_user = self.github_user_obj,
                head_sha = self.source_branch['sha'],
                base_sha = self.target_branch['sha'],
            )
            pull.save()
        return pull

class GithubPullRequestCommentLoader(object):
    """ Parses the payload of the issue_comment webhook and load if issue is a pull request """

    def __init__(self, payload):
        payload = json.loads(payload)


        # We don't care about any issue comments other than pull requests
        if not payload['issue']['pull_request']:
            return

        self.username = payload['comment']['user']['login']
        self.message = payload['comment']['body']
        self.repo_name = payload['repository']['name']
        self.repo_owner = payload['repository']['owner']['login']
        self.repo_url = payload['repository']['git_url']
        self.pull_request = self.repository_obj.call_api('/pulls/%s' % payload['issue']['number'])

    @property
    def repository_obj(self):
        return Repository.objects.get_or_create(
            name = self.repo_name,
            owner = self.repo_owner,
            url = self.repo_url,
        )[0]

    @property
    def source_repository_obj(self):
        source = self.pull_request['head']['repo']
        return Repository.objects.get_or_create(
            name = source['name'],
            owner = source['owner']['login'],
            url = source['git_url'],
        )[0]

    def get_branch_obj(self, branch, repository):
        name = branch['ref'].replace('refs/heads/', '')
        jenkins_name = branch['ref'].replace('ref/heads','origin')
        jenkins_name = jenkins_name.replace('refs/tags','origin/tags')
        return Branch.objects.get_or_create(
            name = name,
            repository = repository,
            github_name = branch['ref'],
            jenkins_name = jenkins_name,
        )[0]

    @property
    def source_branch_obj(self):
        return self.get_branch_obj(self.pull_request['head'], self.source_repository_obj)

    @property
    def target_branch_obj(self):
        return self.get_branch_obj(self.pull_request['base'], self.repository_obj)

    @property
    def pull_request_obj(self):
        repo = self.repository_obj
        number = self.pull_request['number']

        try:
            pull = PullRequest.objects.get(repository=repo, number=number)
        except PullRequest.DoesNotExist:
            pull = PullRequest(
                repository = repo,
                number = number,
                name = self.pull_request['title'],
                message = self.pull_request['body'],
                source_branch = self.source_branch_obj,
                target_branch = self.target_branch_obj,
                github_user = self.pull_request_user_obj,
                head_sha = self.pull_request['head']['sha'],
                base_sha = self.pull_request['base']['sha'],
            )
            pull.save()
        return pull
    
    @property
    def comment_user_obj(self):
        return GithubUser.objects.get_or_create(slug=self.username)[0]

    @property
    def pull_request_user_obj(self):
        return GithubUser.objects.get_or_create(slug=self.pull_request['user']['login'])[0]

    @property
    def comment_obj(self):
        return PullRequestComment.objects.get_or_create(
            pull_request = self.pull_request_obj,
            github_user = self.comment_user_obj,
            message = self.message,
        )[0]
