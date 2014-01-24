import json
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_page
from mrbelvedere.models import JenkinsSite, Job
from mrbelvedere.models import Repository, Branch, BranchJobTrigger
from mrbelvedere.models import PullRequest
from mrbelvedere.utils import GithubPushLoader
from mrbelvedere.utils import GithubPullRequestLoader
from mrbelvedere.utils import GithubPullRequestCommentLoader

GITHUB_WHITELIST = [
    '204.232.175.',
    '192.30.252.',
]

def is_github(request):
    is_github = False

    # If the request was forwarded to a proxy and that is passed in header, 
    # use the HTTP_X_FORWARDED_FOR header instead of REMOTE_ADDR
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        ip_adds = request.META['HTTP_X_FORWARDED_FOR'].split(",")   
        ip = ip_adds[0]
    else:
        ip = request.META['REMOTE_ADDR']

    for subnet in GITHUB_WHITELIST:
        if subnet in ip:
            is_github = True
            break
    if not is_github:
        # FIXME: raise unauthorized
        return HttpResponse('You are not Github, go away!')

def push_webhook(request):
    ip_check = is_github(request)
    if ip_check:
        return ip_check

    data = GithubPushLoader(request.POST['payload'])

    push = data.push_obj

    return HttpResponse('OK')
    
def pull_request_webhook(request):
    ip_check = is_github(request)
    if ip_check:
        return ip_check
    
    data = GithubPullRequestLoader(request.POST.get('payload',None))
    pull_request = data.pull_request_obj
    
    return HttpResponse('OK')

def pull_request_comment_webhook(request):
    ip_check = is_github(request)
    if ip_check:
        return ip_check
    
    data = GithubPullRequestCommentLoader(request.POST.get('payload',None))
    comment = data.comment_obj
    
    return HttpResponse('OK')

def jenkins_jobs(request, slug):
    """ Renders a list of jobs for the current site """
    site = get_object_or_404(JenkinsSite, slug=slug)
    jobs = Job.objects.filter(site = site)
    api_jobs = site.get_api().keys()
    out_of_sync = False
    if len(jobs) != len(api_jobs):
        out_of_sync = True
    
    return render_to_response('jenkins_site/list_jobs.html', {'jobs': jobs, 'out_of_sync': out_of_sync})

def jenkins_update_jobs(request, slug):
    site = get_object_or_404(JenkinsSite, slug=slug)
    site.update_jobs()
    return HttpResponse('Jobs Updated!')

def jenkins_post_build_hook(request, slug):
    site = get_object_or_404(JenkinsSite, slug=slug)

    data = json.loads(request.body)

    build = data['build']
    params = build['parameters']

    status_map = {
        'SUCCESS': {
            'state': 'success',
            'message': 'The build succeeded!',
        },
        'FAILED': {
            'state': 'failure',
            'message': 'The build failed!',
        },
        'UNSUCCESSFUL': {
            'state': 'error',
            'message': 'The build was unsuccessful!',
        },
    }
    status = status_map.get(build['status'], None)
    if not status:
        return HttpResponse('OK')

    # Look for pull requests against the branch and repo
    pulls = PullRequest.objects.filter(
        source_branch__repository__url = params['repository'],
        source_branch__name = params['branch'],
    )

    for pull in pulls:
        # Set the Commit Status so it shows on the pull rqeuest
        pull.repository.call_api('/statuses/%s' % pull.last_build_head_sha, data={
            'state': status['state'],
            'target_url': build['full_url'],
            'description': status['message'],
        })

        # Use a comment on the pull request to report build status and trigger notifications in Github
        pull.repository.call_api('/issues/%s/comments' % pull.number, data={
            'body': '**%s**: %s, view the build at %s' % (status['state'], status['message'], build['full_url']),
        })
        return HttpResponse('OK')        


@cache_page(60*2)
def latest_prod_version(request, owner, repo):
    repo = get_object_or_404(Repository, owner=owner, name=repo)
    return HttpResponse(repo.get_latest_release_name())
    
@cache_page(60*2)
def latest_beta_version(request, owner, repo):
    repo = get_object_or_404(Repository, owner=owner, name=repo)
    return HttpResponse(repo.get_latest_release_name(beta=True))
    
@cache_page(60*2)
def latest_prod_version_tag(request, owner, repo):
    repo = get_object_or_404(Repository, owner=owner, name=repo)
    return HttpResponse(repo.get_latest_release_tag())
    
@cache_page(60*2)
def latest_beta_version_tag(request, owner, repo):
    repo = get_object_or_404(Repository, owner=owner, name=repo)
    return HttpResponse(repo.get_latest_release_tag(beta=True))

def create_repository_webhooks(request, owner, repo):
    repo = get_object_or_404(Repository, owner=owner, name=repo)
    base_url = '%s://%s' % (request.META['wsgi.url_scheme'], request.META['HTTP_HOST'])
    return HttpResponse(repo.create_webhooks(base_url))    

