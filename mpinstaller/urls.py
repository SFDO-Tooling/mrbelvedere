from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^oauth/callback$', 'mpinstaller.views.oauth_callback'),
    url(r'^oauth/login$', 'mpinstaller.views.oauth_login'),
    url(r'^oauth/logout$', 'mpinstaller.views.oauth_logout'),
    url(r'^check_deploy_status$', 'mpinstaller.views.check_deploy_status'),
    url(r'^retrieve_org_packages$', 'mpinstaller.views.retrieve_org_packages'),
    url(r'^retrieve_org_packages/(?P<id>\w+)$', 'mpinstaller.views.retrieve_org_packages_result'),
    url(r'^list_org_metadata/(?P<metatype>[\w|,]+)$', 'mpinstaller.views.list_org_metadata_json'),
    url(r'^(?P<namespace>\w+)$', 'mpinstaller.views.package_overview'),
    url(r'^(?P<namespace>\w+)/uninstall$', 'mpinstaller.views.uninstall_package'),
    url(r'^(?P<namespace>\w+)/(?P<number>.*)/version_install_map$', 'mpinstaller.views.version_install_map'),
    url(r'^(?P<namespace>\w+)/(?P<number>.*)/install$', 'mpinstaller.views.install_package_version'),
    url(r'^(?P<namespace>\w+)/(?P<number>.*)$', 'mpinstaller.views.version_overview'),
)
