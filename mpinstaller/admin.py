from django.contrib import admin
from django import forms
from mpinstaller.models import InstallationError
from mpinstaller.models import InstallationErrorContent
from mpinstaller.models import MetadataCondition
from mpinstaller.models import Package
from mpinstaller.models import PackageInstallation
from mpinstaller.models import PackageInstallationSession
from mpinstaller.models import PackageInstallationStep
from mpinstaller.models import PackageVersion
from mpinstaller.models import PackageVersionDependency
from mpinstaller.models import WhiteList
from mpinstaller.models import WhiteListOrg

class MetadataConditionAdmin(admin.ModelAdmin):
    pass
admin.site.register(MetadataCondition, MetadataConditionAdmin)

class InstallationErrorAdmin(admin.ModelAdmin):
    list_display = ('message', 'content', 'fallback_content')
admin.site.register(InstallationError, InstallationErrorAdmin)

class InstallationErrorContentAdmin(admin.ModelAdmin):
    list_display = ('id', 'resolution')
admin.site.register(InstallationErrorContent, InstallationErrorContentAdmin)

class PackageAdmin(admin.ModelAdmin):
    list_display = ('name','namespace','description')
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
        model = PackageVersion
        widgets = {
            'github_password': forms.PasswordInput(render_value=True),
        }

class PackageVersionAdmin(admin.ModelAdmin):
    list_display = ('package', 'number', 'name')
    list_filter = ('package',)
    form = PackageVersionAdminForm
admin.site.register(PackageVersion, PackageVersionAdmin)

class PackageVersionDependencyAdmin(admin.ModelAdmin):
    list_display = ('version', 'requires', 'order')
    list_filter = ('version__name','requires__name')
admin.site.register(PackageVersionDependency, PackageVersionDependencyAdmin)

class WhiteListAdmin(admin.ModelAdmin):
    list_display = ('name')
admin.site.register(WhiteList, WhiteListAdmin)

class WhiteListOrgAdmin(admin.ModelAdmin):
    list_display = ('whitelist', 'name', 'org_id')
    list_filter = ('whitelist',)
admin.site.register(WhiteListOrg, WhiteListOrgAdmin)
