from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^github/webhook/push/$', 'mrbelvedere.views.push_webhook'),
    url(r'^github/webhook/pull_request/$', 'mrbelvedere.views.pull_request_webhook'),
    url(r'^github/webhook/issue_comment/$', 'mrbelvedere.views.pull_request_comment_webhook'),
    url(r'^jenkins/(?P<slug>\w+)/update_jobs', 'mrbelvedere.views.jenkins_update_jobs'),
    url(r'^repo/(?P<owner>\w+)/(?P<repo>\w+)/webhooks/create$', 'mrbelvedere.views.create_repository_webhooks'),
    url(r'^repo/(?P<owner>\w+)/(?P<repo>\w+)/version/beta/tag$', 'mrbelvedere.views.latest_beta_version_tag'),
    url(r'^repo/(?P<owner>\w+)/(?P<repo>\w+)/version/tag$', 'mrbelvedere.views.latest_prod_version_tag'),
    url(r'^repo/(?P<owner>\w+)/(?P<repo>\w+)/version/beta$', 'mrbelvedere.views.latest_beta_version'),
    url(r'^repo/(?P<owner>\w+)/(?P<repo>\w+)/version$', 'mrbelvedere.views.latest_prod_version'),
)
