from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^github/webhook/$', 'mrbelvedere.views.github_webhook'),
)
