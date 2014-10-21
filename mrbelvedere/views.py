import json
import requests
import datetime
from urllib import quote
from django import forms
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_page
from mrbelvedere.models import JenkinsSite, Job
from mrbelvedere.models import Repository, Branch, BranchJobTrigger
from mrbelvedere.models import PullRequest
from mrbelvedere.models import SalesforceOAuth
from mrbelvedere.models import PackageBuilder, PackageBuilderBuild
from mrbelvedere.utils import GithubPushLoader
from mrbelvedere.utils import GithubPullRequestLoader
from mrbelvedere.utils import GithubPullRequestCommentLoader

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

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

    print 'DEBUG: data = %s' % data

    build = data['build']
    params = build['parameters']

    status_map = {
        'STARTED': {
            'state': 'pending',
            'message': 'The build is running!',
        },
        'SUCCESS': {
            'state': 'success',
            'message': 'The build succeeded!',
        },
        'FAILURE': {
            'state': 'failure',
            'message': 'The build failed!',
        },
        'UNSUCCESSFUL': {
            'state': 'error',
            'message': 'The build was unsuccessful!',
        },
    }

    if build.get('phase',None) == 'STARTED':
        # Jenkins Notifier sends a notification at the start of the build
        # with no status, but phase = STARTED
        status = status_map['STARTED']
    else:
        status = status_map.get(build['status'], None)

    repo_url = params['repository'].replace('git@github.com:','git://github.com/')
    
    # Look for pull requests against the branch and repo
    pulls = PullRequest.objects.filter(
        source_branch__repository__url = repo_url,
        source_branch__name = params['branch'],
    )

    for pull in pulls:
        if status['state'] == 'pending':
            # If we need to set a pending status, the build might be triggering in the background
            # assume it will be building the head commit on the source branch
            resp = pull.repository.call_api('/pulls/%s' % pull.number)

            # Don't save this change because the background job should set it when it completes
            # and we don't want to re-run the triggers
            pull.last_build_head_sha = resp['head']['sha']
        else:
            # Use a comment on the pull request to report build status and trigger notifications in Github
            pull.repository.call_api('/issues/%s/comments' % pull.number, data={
                'body': '**%s**: %s, view the build at %s' % (status['state'], status['message'], build['full_url']),
            })

        # Set the Commit Status so it shows on the pull request
        resp = pull.repository.call_api('/statuses/%s' % pull.last_build_head_sha, data={
            'state': status['state'],
            'target_url': build['full_url'],
            'description': status['message'],
        })

        print resp

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

@cache_page(60*2)
def job_build_status(request, site, job):
    job = get_object_or_404(Job, site__slug=site, name=job)
    icon = requests.get('%s/buildStatus/icon?job=%s' % (job.site.url, job.name), auth=(job.site.user, job.site.password))
    response = HttpResponse(content=icon.content, mimetype=icon.headers['content-type'])
    return response

class CreatePackageBuilderForm(forms.ModelForm):
    namespace = forms.CharField
    
    class Meta:
        model = PackageBuilder
        fields = ['repository','namespace','package_name','key','org']

    def __init__(self, oauth, *args, **kwargs):
        super(CreatePackageBuilderForm, self).__init__(*args, **kwargs)
        self.fields['org'].initial = self.get_or_create_org(oauth).id
        self.fields['org'].widget = forms.HiddenInput()

    def get_or_create_org(self, oauth):
        try:
            org = SalesforceOAuth.objects.get(oauth_id = oauth['id'], scope__contains='web')
        except SalesforceOAuth.DoesNotExist:
            org = SalesforceOAuth(
                oauth_id = oauth['id'],
                username = oauth['username'],
                org_name = oauth['org_name'],
                org_id = oauth['org_id'],
                org_type = oauth['org_type'],
                instance_url = oauth['instance_url'],
                scope = oauth['scope'],
                access_token = oauth['access_token'],
                refresh_token = oauth['refresh_token'],
            )
            org.save()
        return org

def create_package_builder(request):
    oauth = request.session.get('oauth', None)
    if not oauth:
        redirect = quote(request.build_absolute_uri('/mrbelvedere/package-builder/create'))
        return HttpResponseRedirect('/mpinstaller/oauth/login?scope=full%%20refresh_token%%20web&redirect=%s' % redirect)
    if request.method == 'POST':
        form = CreatePackageBuilderForm(oauth, request.POST)
        form.save()
        return HttpResponseRedirect(request.build_absolute_uri('/mrbelvedere/package-builder/%s' % form.instance.namespace))
    else:
        form = CreatePackageBuilderForm(oauth)
        redirect = quote(request.build_absolute_uri('/mrbelvedere/package-builder/create'))
        data = {
            'form': form,
            'oauth': oauth,
            'logout_url': request.build_absolute_uri('/mpinstaller/oauth/login?redirect=%s' % redirect),
        }
        return render_to_response('mrbelvedere/create_package_builder.html', data)

def package_builder_overview(request, namespace):
    builder = get_object_or_404(PackageBuilder, namespace=namespace)
    data = {
        'builder': builder,
        'recent_builds': builder.builds.order_by('-created')[:10],
    }
    return render_to_response('mrbelvedere/package_builder_overview.html', data)

def package_builder_build(request, namespace):
    builder = get_object_or_404(PackageBuilder, namespace=namespace)

    if builder.key != request.META.get('HTTP_AUTHORIZATION', None):
        return HttpResponse('Unauthorized', status=401)

    # Block concurrent builds
    active_builds = builder.builds.exclude(status__in = ['Complete','Failed']).count()
    if active_builds:
        return HttpResponse('ERROR: A build is already running for this package')
    
    name = request.GET.get('name','Beta Release')
    revision = request.GET.get('revision',None)

    build = PackageBuilderBuild(
        builder = builder,
        name = name,
        revision = revision,
    )
    build.save()
    return HttpResponseRedirect(request.build_absolute_uri('/mrbelvedere/package-builder/%s/build/%s' % (builder.namespace, build.id)))

def package_builder_build_status(request, namespace, id):
    build = get_object_or_404(PackageBuilderBuild, builder__namespace=namespace, id=id)

    # Handle json response
    format = request.GET.get('format', None)
    if format == 'json':
        dthandler = lambda obj: (
            obj.isoformat()
            if isinstance(obj, datetime.datetime)
            or isinstance(obj, datetime.date)
            else None)
        return HttpResponse(json.dumps(build.__dict__, default=dthandler), content_type="application/json")

    data = {
        'build': build,
    }
    return render_to_response('mrbelvedere/package_builder_build.html', data)
