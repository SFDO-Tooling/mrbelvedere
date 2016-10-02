from django.contrib import admin

from django import forms
from django.db import models
from mpinstaller.models import InstallationError
from mpinstaller.models import InstallationErrorContent
from mpinstaller.models import MetadataCondition
from mpinstaller.models import Package
from mpinstaller.models import PackageInstallation
from mpinstaller.models import PackageInstallationSession
from mpinstaller.models import PackageInstallationStep
from mpinstaller.models import PackageVersion
from mpinstaller.models import PackageVersionDependency

class MetadataConditionAdmin(admin.ModelAdmin):
    pass
admin.site.register(MetadataCondition, MetadataConditionAdmin)

class InstallationErrorContentAdmin(admin.ModelAdmin):
    list_display = ('id', 'resolution')
admin.site.register(InstallationErrorContent, InstallationErrorContentAdmin)

class InstallationErrorAdmin(admin.ModelAdmin):
    list_display = ('message', 'content', 'fallback_content')
admin.site.register(InstallationError, InstallationErrorAdmin)


class PackageAdmin(admin.ModelAdmin):
    list_display = ('name','namespace','description')
    fieldsets = (
        (None, {
            'fields': ('namespace','name','description'),
        }),
        ('Content', {
            'classes': ('collapse',),
            'fields': ('content_intro','content_success','content_failure'),
        }),
        ('Content (Beta Overrides)', {
            'classes': ('collapse',),
            'fields': ('content_intro_beta','content_success_beta','content_failure_beta'),
        }),
        ('Current Versions', {
            'classes': ('collapse',),
            'fields': ('current_prod','current_beta','current_github'),
        }),
        ('Config Options', {
            'classes': ('collapse',),
            'fields': ('key','force_sandbox'),
        }),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        try:
            obj_id = request.resolver_match.args[0]
        except IndexError:
            obj_id = None

        if db_field.name == "current_prod":
            if obj_id:
                kwargs["queryset"] = PackageVersion.objects.filter(
                    models.Q(package = obj_id, repo_url__isnull = True) &
                    ~models.Q(number__contains = 'Beta'),
                )
            else:
                kwargs["queryset"] = PackageVersion.objects.none()
        if db_field.name == "current_beta":
            if obj_id:
                kwargs["queryset"] = PackageVersion.objects.filter(
                    package = obj_id,
                    number__contains = 'Beta',
                )
            else:
                kwargs["queryset"] = PackageVersion.objects.none()
        if db_field.name == "current_github":
            if obj_id:
                kwargs["queryset"] = PackageVersion.objects.filter(
                    package = obj_id,
                    repo_url__isnull = False,
                )
            else:
                kwargs["queryset"] = PackageVersion.objects.none()
        return super(PackageAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(Package, PackageAdmin)

class PackageInstallationAdmin(admin.ModelAdmin):
    list_display = ('package','version','username','org_type','status','log', 'created', 'modified')
    list_filter = ('package','status','username','org_type')
admin.site.register(PackageInstallation, PackageInstallationAdmin)

class PackageInstallationSessionAdmin(admin.ModelAdmin):
    list_display = ('installation',)
admin.site.register(PackageInstallationSession, PackageInstallationSessionAdmin)

class PackageInstallationStepAdmin(admin.ModelAdmin):
    list_display = ('id', 'package','installation','version','status','action','created','modified')
    list_filter = ('package','status','action')
admin.site.register(PackageInstallationStep, PackageInstallationStepAdmin)

class PackageVersionAdminForm(forms.ModelForm):
    class Meta:
        fields = [
            'package',
            'name',
            'number',
            'zip_url',
            'repo_url',
            'github_username',
            'github_password',
            'branch',
            'subfolder',
            'namespace_token',
            'namespace',
            'package_name',
            'conditions',
            'content_intro',
            'content_success',
            'content_failure',
        ]
        model = PackageVersion
        widgets = {
            'github_password': forms.PasswordInput(render_value=True),
        }

class PackageVersionAdmin(admin.ModelAdmin):
    list_display = ('package', 'number', 'name')
    list_filter = ('package',)
    fieldsets = (
        (None, {
            'fields': ('package',),
        }),
        ('Managed Package Version', {
            'classes': ('collapse',),
            'fields': ('number',),
        }),
        ('Metadata from Zip File', {
            'classes': ('collapse',),
            'fields': ('zip_url',),
        }),
        ('Metadata from Github', {
            'classes': ('collapse',),
            'fields': ('repo_url','github_username','github_password','branch','subfolder','package_name','namespace_token','namespace'),
        }),
        ('Version Specific Content', {
            'classes': ('collapse',),
            'fields': ('content_intro','content_success','content_failure'),
        }),
        ('Metadata Conditions', {
            'classes': ('collapse',),
            'fields': ('conditions',),
        }),
    )
    form = PackageVersionAdminForm
admin.site.register(PackageVersion, PackageVersionAdmin)

class PackageVersionDependencyAdmin(admin.ModelAdmin):
    list_display = ('version', 'requires', 'order')
    list_filter = ('version__name','requires__name')
admin.site.register(PackageVersionDependency, PackageVersionDependencyAdmin)
