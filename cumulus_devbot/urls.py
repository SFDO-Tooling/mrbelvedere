from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
admin.autodiscover()

#urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'cumulus_devbot.views.home', name='home'),
    # url(r'^cumulus_devbot/', include('cumulus_devbot.foo.urls')),
#)


urlpatterns = [
    url(r'^$', 'mpinstaller.views.redirect_to_package_list'),
    url(r'^api/', include('api.urls')),
    url(r'^mrbelvedere/', include('mrbelvedere.urls')),
    url(r'^mpinstaller/', include('mpinstaller.urls')),
    url(r'^contributor/', include('contributor.urls')),
    url(r'^django-rq/', include('django_rq.urls')),
    url(r'^tinymce/', include('tinymce.urls')),

    # django admin routes
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^social-auth/', include('social_auth.urls')),

    # ... the rest of your URLconf goes here ...
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
