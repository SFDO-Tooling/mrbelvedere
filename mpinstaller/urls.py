from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^installation/(?P<installation_id>\w+)$', 'mpinstaller.views.installation_overview'),
    url(r'^oauth/callback$', 'mpinstaller.views.oauth_callback'),
    url(r'^oauth/login$', 'mpinstaller.views.oauth_login'),
    url(r'^oauth/post_login$', 'mpinstaller.views.oauth_post_login'),
    url(r'^oauth/logout$', 'mpinstaller.views.oauth_logout'),
    url(r'^org/user$', 'mpinstaller.views.org_user'),
    url(r'^org/org$', 'mpinstaller.views.org_org'),
    url(r'^org/packages$', 'mpinstaller.views.org_packages'),
    url(r'^org/condition_metadata/(?P<version_id>\w+)$', 'mpinstaller.views.org_condition_metadata'),
    url(r'^(?P<namespace>\w+)$', 'mpinstaller.views.package_overview'),
    url(r'^(?P<namespace>\w+)/beta$', 'mpinstaller.views.package_overview', {'beta': True}),
    url(r'^(?P<namespace>\w+)/dependencies$', 'mpinstaller.views.package_dependencies'),
    url(r'^(?P<namespace>\w+)/dependencies/beta$', 'mpinstaller.views.package_dependencies', {'beta': True}),
    url(r'^(?P<namespace>\w+)/version/(?P<version_id>\w+)/install$', 'mpinstaller.views.start_package_installation'),
)
