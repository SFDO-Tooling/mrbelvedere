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
from mrbelvedere.models import PullRequest
from mrbelvedere.models import PullRequestComment
from mrbelvedere.models import RepositoryPullRequestJob

class JenkinsSiteAdmin(admin.ModelAdmin):
    list_display = ('slug','url','user')
admin.site.register(JenkinsSite, JenkinsSiteAdmin)

class JobAdmin(admin.ModelAdmin):
    list_display = ('name','site')
admin.site.register(Job, JobAdmin)

class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('name','url')
admin.site.register(Repository, RepositoryAdmin)

class RepositoryNewBranchJobAdmin(admin.ModelAdmin):
    list_display = ('id','repository','job')
admin.site.register(RepositoryNewBranchJob, RepositoryNewBranchJobAdmin)

class BranchAdmin(admin.ModelAdmin):
    list_display = ('name','repository')
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

class PullRequestAdmin(admin.ModelAdmin):
    list_display = ('id','name','number','source_branch','target_branch', 'github_user')
admin.site.register(PullRequest, PullRequestAdmin)

class PullRequestCommentAdmin(admin.ModelAdmin):
    list_display = ('id','pull_request','github_user')
admin.site.register(PullRequestComment, PullRequestCommentAdmin)

class RepositoryPullRequestJobAdmin(admin.ModelAdmin):
    list_display = ('id','repository','job','forked','internal','moderated')
admin.site.register(RepositoryPullRequestJob, RepositoryPullRequestJobAdmin)
