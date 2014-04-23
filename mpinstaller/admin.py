from django.contrib import admin
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

class PackageAdmin(admin.ModelAdmin):
    list_display = ('name','namespace','description')
admin.site.register(Package, PackageAdmin)

class PackageInstallationAdmin(admin.ModelAdmin):
    list_display = ('package','version','username','org_type','status')
admin.site.register(PackageInstallation, PackageInstallationAdmin)

class PackageInstallationSessionAdmin(admin.ModelAdmin):
    list_display = ('installation',)
admin.site.register(PackageInstallationSession, PackageInstallationSessionAdmin)

class PackageInstallationStepAdmin(admin.ModelAdmin):
    list_display = ('id', 'package','installation','version','status','action','created','modified')
    list_filter = ('package','status','action')
admin.site.register(PackageInstallationStep, PackageInstallationStepAdmin)

class PackageVersionAdmin(admin.ModelAdmin):
    list_display = ('package', 'number', 'name')
    list_filter = ('package',)
admin.site.register(PackageVersion, PackageVersionAdmin)

class PackageVersionDependencyAdmin(admin.ModelAdmin):
    list_display = ('version', 'requires', 'order')
    list_filter = ('version__package__name','requires__package__name')
admin.site.register(PackageVersionDependency, PackageVersionDependencyAdmin)
