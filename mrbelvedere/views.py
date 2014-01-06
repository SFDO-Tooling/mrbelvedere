import json
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from mrbelvedere.models import JenkinsSite, Job
from mrbelvedere.models import Repository, Branch, BranchJobTrigger
from mrbelvedere.utils import GithubWebhookParser

GITHUB_WHITELIST = [
    '204.232.175.',
    '192.30.252.',
]

def github_webhook(request):
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

    data = GithubWebhookParser(request.POST['payload'])
    push = data.push_obj

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

def latest_prod_version(request, slug):
    repo = get_object_or_404(Repository, slug=slug)
    return HttpResponse(repo.get_latest_release())
    
def latest_beta_version(request, slug):
    repo = get_object_or_404(Repository, slug=slug)
    return HttpResponse(repo.get_latest_release(beta=True))
    
