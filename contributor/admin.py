from django.contrib import admin
from contributor.models import Contribution
from contributor.models import ContributionSync

class ContributionAdmin(admin.ModelAdmin):
    pass
admin.site.register(Contribution, ContributionAdmin)

class ContributionSyncAdmin(admin.ModelAdmin):
    pass
admin.site.register(ContributionSync, ContributionSyncAdmin)

