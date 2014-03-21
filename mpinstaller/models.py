from django.db import models

class MetadataCondition(models.Model):
    metadata_type = models.CharField(max_length=255)
    field = models.CharField(max_length=255)
    search = models.CharField(max_length=255)
    exclude_namespaces = models.CharField(max_length=255)
    method = models.CharField(max_length=255, null=True, blank=True)
    no_match = models.BooleanField(default=False)

    def __unicode__(self):
        method = 'is'
        if self.no_match:
            method = 'is not'
        if self.method:
            method = self.method
            if self.no_match:
                method = 'not %s' % method

        excluding = ''
        if self.exclude_namespaces:
            excluding = ' excluding namespaces %s' % self.exclude_namespaces

        return '%s where %s %s "%s"%s' % (
            self.metadata_type,
            self.field,
            method,
            self.search,
            excluding,
        )

class Package(models.Model):
    namespace = models.SlugField()
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    current_prod = models.ForeignKey('mpinstaller.PackageVersion', related_name='current_prod', null=True, blank=True)
    current_beta = models.ForeignKey('mpinstaller.PackageVersion', related_name='current_beta', null=True, blank=True)
    key = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return '%s (%s)' % (self.name, self.namespace)

    def get_dependencies(self, beta):
        if not beta and not self.current_prod:
            raise LookupError('No current_prod found')
        if beta and not self.current_beta:
            raise LookupError('No current_beta found')
        
        if beta: 
            parent = self.current_beta
        else:
            parent = self.current_prod

        dependencies = []

        for version in parent.dependencies.all():
            dependencies.append({
                'namespace': version.requires.package.namespace,
                'number': version.requires.number,
                'zip_url': version.requires.zip_url,
            })

        dependencies.append({
            'namespace': self.namespace,
            'number': parent.number,
            'zip_url': parent.zip_url,
        })
        return dependencies
        
    def update_dependencies(self, beta, dependencies):
        if beta: 
            parent = self.current_beta
        else:
            parent = self.current_prod

        versions = {}
        for dependency in parent.dependencies.all():
            versions[version.package.namespace] = dependency.requires

        # Start the order at 10 leaving room for manual dependencies
        order = 10

        for dependency in dependencies:
            version = versions.get(dependency['namespace'])
            if not version:
                # We don't create new dependencies through this process, only update existing ones
                continue

            version.number = dependency.get('number',None)
            version.zip_url = dependency.get('zip_url',None)
            version.order = order
            version.save()

            order = order + 10
    
        return self.get_dependencies(beta)

    class Meta:
        ordering = ['namespace',]

class PackageVersion(models.Model):
    package = models.ForeignKey(Package, related_name='versions')
    name = models.CharField(max_length=255)
    number = models.CharField(max_length=32, null=True, blank=True)
    zip_url = models.URLField(null=True, blank=True)
    subdir = models.CharField(max_length=255, null=True, blank=True)
    conditions = models.ManyToManyField(MetadataCondition, null=True, blank=True)

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

class PackageInstallation(models.Model):
    package = models.ForeignKey(Package)
    version = models.ForeignKey(PackageVersion, null=True, blank=True)
    action = models.CharField(max_length=32)
    org_id = models.CharField(max_length=32)
    org_type = models.CharField(max_length=255)
    status = models.CharField(max_length=32)
    username = models.CharField(max_length=255)
    log = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
