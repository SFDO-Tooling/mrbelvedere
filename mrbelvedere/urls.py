from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^github/webhook/$', 'mrbelvedere.views.github_webhook'),
    url(r'^jenkins/(?P<slug>\w+)/update_jobs', 'mrbelvedere.views.jenkins_update_jobs'),
)
