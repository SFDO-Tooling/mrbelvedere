from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^github/webhook/push/$', 'mrbelvedere.views.push_webhook'),
    url(r'^github/webhook/pull_request/$', 'mrbelvedere.views.pull_request_webhook'),
    url(r'^github/webhook/issue_comment/$', 'mrbelvedere.views.pull_request_comment_webhook'),
    url(r'^jenkins/(?P<slug>\w+)/update_jobs$', 'mrbelvedere.views.jenkins_update_jobs'),
    url(r'^jenkins/(?P<slug>\w+)/post_build_webhook$', 'mrbelvedere.views.jenkins_post_build_hook'),
    url(r'^jenkins/(?P<site>[-\w]+)/(?P<job>[-\w]+)/status$', 'mrbelvedere.views.job_build_status'),
    url(r'^repo/(?P<owner>[-\w]+)/(?P<repo>[-_\w]+)/webhooks/create$', 'mrbelvedere.views.create_repository_webhooks'),
    url(r'^repo/(?P<owner>[-\w]+)/(?P<repo>[-_\w]+)/version/beta/tag$', 'mrbelvedere.views.latest_beta_version_tag'),
    url(r'^repo/(?P<owner>[-\w]+)/(?P<repo>[-_\w]+)/version/tag$', 'mrbelvedere.views.latest_prod_version_tag'),
    url(r'^repo/(?P<owner>[-\w]+)/(?P<repo>[-_\w]+)/version/beta$', 'mrbelvedere.views.latest_beta_version'),
    url(r'^repo/(?P<owner>[-\w]+)/(?P<repo>[-_\w]+)/version$', 'mrbelvedere.views.latest_prod_version'),
    url(r'^package-builder/create$', 'mrbelvedere.views.create_package_builder'),
    url(r'^package-builder/(?P<namespace>\w+)$', 'mrbelvedere.views.package_builder_overview'),
    url(r'^package-builder/(?P<namespace>\w+)/build$', 'mrbelvedere.views.package_builder_build'),
    url(r'^package-builder/(?P<namespace>\w+)/build/(?P<id>\w+)$', 'mrbelvedere.views.package_builder_build_status'),
)
