from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'cumulus_devbot.views.home', name='home'),
    # url(r'^cumulus_devbot/', include('cumulus_devbot.foo.urls')),
    url(r'^mrbelvedere/', include('mrbelvedere.urls')),
    url(r'^orgbuilder/', include('orgbuilder.urls')),

    # django admin routes
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url('^django-rq/', include('django_rq.urls')),
)
