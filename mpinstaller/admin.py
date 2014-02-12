from django.contrib import admin
from mpinstaller.models import Package
from mpinstaller.models import PackageVersion
from mpinstaller.models import PackageVersionDependency

class PackageAdmin(admin.ModelAdmin):
    list_display = ('name','namespace','description')
admin.site.register(Package, PackageAdmin)

class PackageVersionAdmin(admin.ModelAdmin):
    list_display = ('package', 'number', 'name')
    list_filter = ('package','beta')
admin.site.register(PackageVersion, PackageVersionAdmin)

class PackageVersionDependencyAdmin(admin.ModelAdmin):
    list_display = ('version', 'requires', 'order')
    list_filter = ('version__package__name','requires__package__name')
admin.site.register(PackageVersionDependency, PackageVersionDependencyAdmin)
