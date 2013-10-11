from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^dev/new/$', 'orgbuilder.views.dev_new'),
)
