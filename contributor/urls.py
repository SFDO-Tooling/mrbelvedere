from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^$', 'contributor.views.contributor_home'),
    url(r'^create$', 'contributor.views.create_contribution'),
    url(r'^contributions/(?P<contribution_id>\d+)$', 'contributor.views.contribution'),
    url(r'^contributions/(?P<contribution_id>\d+)/edit_branch$', 'contributor.views.contribution_edit_branch'),
    url(r'^contributions/(?P<contribution_id>\d+)/edit_salesforce_org$', 'contributor.views.contribution_edit_salesforce_org'),
    url(r'^contributions/(?P<contribution_id>\d+)/capture_salesforce_org$', 'contributor.views.contribution_capture_salesforce_org'),
    url(r'^contributions/(?P<contribution_id>\d+)/commit$', 'contributor.views.contribution_commit'),
    url(r'^contributions/(?P<contribution_id>\d+)/syncs$', 'contributor.views.contribution_syncs'),
    url(r'^contributions/(?P<contribution_id>\d+)/sync-state$', 'contributor.views.contribution_sync_state'),
    url(r'^contributions/(?P<contribution_id>\d+)/status$', 'contributor.views.contribution_status'),
    url(r'^contributions/(?P<contribution_id>\d+)/check-state$', 'contributor.views.contribution_check_state'),
    url(r'^(?P<username>\w+)$', 'contributor.views.contributor_contributions'),
)
