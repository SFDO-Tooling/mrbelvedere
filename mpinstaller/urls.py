from django.conf.urls import url
from mpinstaller import views

urlpatterns = [
    url(r'^$', views.package_list),
    url(r'^installation/(?P<installation_id>\w+)$', views.installation_overview),
    url(r'^oauth/callback$', views.oauth_callback),
    url(r'^oauth/login$', views.oauth_login),
    url(r'^oauth/post_login$', views.oauth_post_login),
    url(r'^oauth/logout$', views.oauth_logout),
    url(r'^oauth/refresh$', views.oauth_refresh),
    url(r'^org/user$', views.org_user),
    url(r'^org/org$', views.org_org),
    url(r'^org/packages$', views.org_packages),
    url(r'^org/condition_metadata/(?P<version_id>\w+)$', views.org_condition_metadata),
    url(r'^(?P<namespace>[A-Za-z0-9_][A-Za-z0-9_]*)$', views.package_overview),
    url(r'^(?P<namespace>[A-Za-z0-9_][A-Za-z0-9_]*)/beta$', views.package_overview, {'beta': True}),
    url(r'^(?P<namespace>[A-Za-z0-9_][A-Za-z0-9_]*)/github$', views.package_overview, {'github': True}),
    url(r'^(?P<namespace>[A-Za-z0-9_][A-Za-z0-9_]*)/stats$', views.package_stats),
    url(r'^(?P<namespace>[A-Za-z0-9_][A-Za-z0-9_]*)/errors$', views.package_errors),
    url(r'^(?P<namespace>[A-Za-z0-9_][A-Za-z0-9_]*)/dependencies$', views.package_dependencies),
    url(r'^(?P<namespace>[A-Za-z0-9_][A-Za-z0-9_]*)/dependencies/beta$', views.package_dependencies, {'beta': True}),
    url(r'^(?P<namespace>[A-Za-z0-9_][A-Za-z0-9_]*)/version/(?P<version_id>\w+)$', views.package_version_overview),
    url(r'^(?P<namespace>[A-Za-z0-9_][A-Za-z0-9_]*)/version/(?P<version_id>\w+)/install$', views.start_package_installation),
    url(r'^(?P<namespace>[A-Za-z0-9_][A-Za-z0-9_]*)/version/(?P<version_id>\w+)/installation-unavailable/(?P<reason>.*)$', views.installation_unavailable),
]
