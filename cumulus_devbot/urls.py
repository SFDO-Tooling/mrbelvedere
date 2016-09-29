from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from mpinstaller.views import redirect_to_package_list
admin.autodiscover()

urlpatterns = [
    url(r'^$', redirect_to_package_list),
    url(r'^api/', include('api.urls')),
    url(r'^mpinstaller/', include('mpinstaller.urls')),
    url(r'^contributor/', include('contributor.urls')),
    url(r'^django-rq/', include('django_rq.urls')),
    url(r'^tinymce/', include('tinymce.urls')),
    url('', include('social.apps.django_app.urls', namespace='social')),

    # django admin routes
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', admin.site.urls),

    # ... the rest of your URLconf goes here ...
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
