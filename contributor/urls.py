from django.conf.urls import url
from contributor import views

urlpatterns = [
    url(r'^$', views.contributor_home),
    url(r'^create$', views.create_contribution),
    url(r'^contributions/(?P<contribution_id>\d+)$', views.contribution),
    url(r'^contributions/(?P<contribution_id>\d+)/edit_branch$', views.contribution_edit_branch),
    url(r'^contributions/(?P<contribution_id>\d+)/edit_salesforce_org$', views.contribution_edit_salesforce_org),
    url(r'^contributions/(?P<contribution_id>\d+)/capture_salesforce_org$', views.contribution_capture_salesforce_org),
    url(r'^contributions/(?P<contribution_id>\d+)/commit$', views.contribution_commit),
    url(r'^contributions/(?P<contribution_id>\d+)/submit$', views.contribution_submit),
    url(r'^contributions/(?P<contribution_id>\d+)/syncs$', views.contribution_syncs),
    url(r'^contributions/(?P<contribution_id>\d+)/sync-state$', views.contribution_sync_state),
    url(r'^contributions/(?P<contribution_id>\d+)/status$', views.contribution_status),
    url(r'^contributions/(?P<contribution_id>\d+)/check-state$', views.contribution_check_state),
    url(r'^(?P<username>\w+)$', views.contributor_contributions),
]
