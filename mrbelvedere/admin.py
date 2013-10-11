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
    list_display = ('slug','url','user')
admin.site.register(JenkinsSite, JenkinsSiteAdmin)

class JobAdmin(admin.ModelAdmin):
    list_display = ('slug','site')
admin.site.register(Job, JobAdmin)

class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('slug','url')
admin.site.register(Repository, RepositoryAdmin)

class RepositoryNewBranchJobAdmin(admin.ModelAdmin):
    list_display = ('id','repository','job')
admin.site.register(RepositoryNewBranchJob, RepositoryNewBranchJobAdmin)

class BranchAdmin(admin.ModelAdmin):
    list_display = ('slug','repository')
admin.site.register(Branch, BranchAdmin)

class BranchJobTriggerAdmin(admin.ModelAdmin):
    list_display = ('id','branch','job','active','last_trigger_date')
admin.site.register(BranchJobTrigger, BranchJobTriggerAdmin)

class GithubUserAdmin(admin.ModelAdmin):
    list_display = ('id','slug','name','email')
admin.site.register(GithubUser, GithubUserAdmin)

class PushAdmin(admin.ModelAdmin):
    list_display = ('id','branch','github_user','message')
    list_filter = ('branch','branch__repository','github_user')
admin.site.register(Push, PushAdmin)
