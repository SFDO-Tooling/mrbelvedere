from django.db import models

class Package(models.Model):
    namespace = models.SlugField()
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    current_prod = models.ForeignKey('mpinstaller.PackageVersion', related_name='current_prod', null=True, blank=True)
    current_beta = models.ForeignKey('mpinstaller.PackageVersion', related_name='current_beta', null=True, blank=True)

    def __unicode__(self):
        return '%s (%s)' % (self.name, self.namespace)

    class Meta:
        ordering = ['namespace',]

class PackageVersion(models.Model):
    package = models.ForeignKey(Package, related_name='versions')
    beta = models.BooleanField(default=False)
    name = models.CharField(max_length=255)
    number = models.CharField(max_length=32)

    def __unicode__(self):
        return '%s (%s)' % (self.number, self.package.namespace)

    class Meta:
        ordering = ['package__namespace','number']

class PackageVersionDependency(models.Model):
    version = models.ForeignKey(PackageVersion, related_name='dependencies')
    requires = models.ForeignKey(PackageVersion, related_name='required_by')
    order = models.IntegerField()

    def __unicode__(self):
        return '%s (%s) requires %s (%s)' % (
            self.version.number,
            self.version.package.namespace,
            self.requires.number,
            self.requires.package.namespace,
        )

    class Meta:
        ordering = ['order',]
