from django.contrib import admin
from mrbelvedere.models import JenkinsSite
from mrbelvedere.models import Job
from mrbelvedere.models import Repository
from mrbelvedere.models import RepositoryNewBranchJob
from mrbelvedere.models import Branch
from mrbelvedere.models import BranchJobTrigger
from mrbelvedere.models import BranchJobTrigger
from mrbelvedere.models import GithubUser
from mrbelvedere.models import Push

class JenkinsSiteAdmin(admin.ModelAdmin):
    pass
admin.site.register(JenkinsSite, JenkinsSiteAdmin)

class JobAdmin(admin.ModelAdmin):
    pass
admin.site.register(Job, JobAdmin)

class RepositoryAdmin(admin.ModelAdmin):
    pass
admin.site.register(Repository, RepositoryAdmin)

class RepositoryNewBranchJobAdmin(admin.ModelAdmin):
    pass
admin.site.register(RepositoryNewBranchJob, RepositoryNewBranchJobAdmin)

class BranchAdmin(admin.ModelAdmin):
    pass
admin.site.register(Branch, BranchAdmin)

class BranchJobTriggerAdmin(admin.ModelAdmin):
    pass
admin.site.register(BranchJobTrigger, BranchJobTriggerAdmin)

class GithubUserAdmin(admin.ModelAdmin):
    pass
admin.site.register(GithubUser, GithubUserAdmin)

class PushAdmin(admin.ModelAdmin):
    pass
admin.site.register(Push, PushAdmin)
