from django.contrib import admin
from contributor.models import Contribution
from contributor.models import ContributionSync

class ContributionAdmin(admin.ModelAdmin):
    list_display = ('id','package_version','contributor','github_issue','fork_branch','title', 'date_started', 'date_modified')
    list_filter = ('package_version','contributor')
admin.site.register(Contribution, ContributionAdmin)

class ContributionSyncAdmin(admin.ModelAdmin):
    list_display = ('id','contribution','status','message','new_commit','new_installation')
    list_filter = ('contribution__package_version','contribution__contributor','status')
admin.site.register(ContributionSync, ContributionSyncAdmin)

