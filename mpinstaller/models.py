from django.db import models
from tinymce.models import HTMLField

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
    content_intro = HTMLField(null=True, blank=True, help_text="Shown on the page to start an installation in the Package Information panel if provided.")
    content_success = HTMLField(null=True, blank=True, help_text="Shown on the installation status page after a successful installation in the Next Steps panel if provided.")
    content_failure = HTMLField(null=True, blank=True, help_text="Shown on the installation status page after a failed installation in the Next Steps panel if provided.")
    content_success_beta = HTMLField(null=True, blank=True, help_text="Shown instead of Content success if the package is a beta.")
    content_failure_beta = HTMLField(null=True, blank=True, help_text="Shown instead of Content failure if the package is a beta.")

    def __unicode__(self):
        return self.name

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
            versions[dependency.requires.package.namespace] = dependency.requires
        versions[self.namespace] = parent

        # Start the order at 10 leaving room for manual dependencies
        order = 10

        for dependency in dependencies:
            version = versions.get(dependency['namespace'])
            if not version:
                # We don't create new dependencies through this process, only update existing ones
                continue

            number = dependency.get('number',None)
            if number:
                version.name = number
            version.number = number
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
    conditions = models.ManyToManyField(MetadataCondition, null=True, blank=True)
    content_intro = HTMLField(null=True, blank=True, help_text="Optional version specific text to show in Package Information panel")
    content_success = HTMLField(null=True, blank=True, help_text="Optional version specific text shown after a successful installation.")
    content_failure = HTMLField(null=True, blank=True, help_text="Optional version specific text shown after a failed installation.")

    def __unicode__(self):
        if self.number:
            return '%s %s (%s)' % (self.name, self.number, self.package.namespace)
        return self.name

    def is_beta(self):
        if self.number and self.number.find('(Beta ') != -1:
            return True
        return False

    def get_installer_url(self, request=None):
        redirect = None
        if self.package.current_prod and self.package.current_prod.id == self.id:
            redirect = '/mpinstaller/%s' %  self.package.namespace
        elif self.package.current_beta and self.package.current_beta.id == self.id:
            redirect = '/mpinstaller/%s/beta' %  self.package.namespace
        else:
            redirect = '/mpinstaller/%s/version/%s' %  (namespace, self.id)
        if request:
            redirect = request.build_absolute_uri(redirect)
        if redirect:
            return redirect

    def check_conditions(self, metadata):
        passes = True
        
        for condition in self.conditions.all():
            matched = False
            exclude_namespaces = []
            if condition.exclude_namespaces:
                exclude_namespaces = condition.exclude_namespaces.split(',')
            for item in metadata[condition.metadata_type]:
                if item.get('namespace','') in exclude_namespaces:
                    continue
        
                value = item.get(condition.field, None)
                if not value:
                    continue
        
                # If no method was provided, do a straight string compare
                if not condition.method:
                    if value == condition.search:
                        matched = True
                else:
                    # Lookup the method dynamically and call it with the search string
                    method = getattr(value, condition.method)
                    if method(condition.search):
                        matched = True
        
            if condition.no_match and matched:
                passes = False
            elif not condition.no_match and not modified:
                passes = False

        return passes

    def get_content_intro(self):
        # Look for content from the package
        content = []
        if self.package.content_intro:
            content.append(self.package.content_intro)

        # Append version specific information if available
        if self.content_intro:
            content.append(self.content_intro)

        if content:
            return {
                'heading': self.package.name,
                'body': '\n'.join(content),
            }

    def get_content_success(self):
        # Look for content from the package
        content = []
        if self.is_beta():
            if self.package.content_success_beta:
                content.append(self.package.content_success_beta)
        if not content and self.package.content_success:
            content.append(self.package.content_success)

        # Append version specific information if available
        if self.content_success:
            content.append(self.content_success)

        if content:
            return {
                'heading': self.package.name,
                'body': '\n'.join(content),
            }

    def get_content_failure(self):
        # Look for content from the package
        content = []
        if self.is_beta():
            if self.package.content_failure_beta:
                content.append(self.package.content_failure_beta)
        if not content and self.package.content_failure:
            content.append(self.package.content_failure)

        # Append version specific information if available
        if self.content_failure:
            content.append(self.content_failure)

        if content:
            return {
                'heading': self.package.name,
                'body': '\n'.join(content),
            }

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
    package = models.ForeignKey(Package, related_name='installations')
    version = models.ForeignKey(PackageVersion, related_name='installations', null=True, blank=True)
    org_id = models.CharField(max_length=32)
    org_type = models.CharField(max_length=255)
    status = models.CharField(max_length=32)
    username = models.CharField(max_length=255)
    install_map = models.TextField(null=True, blank=True)
    log = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s: Install %s' % (self.id, self.version)

    def get_progress(self):
        if self.status in ['Succeeded','Failed','Cancelled']:
            return 100
        if self.status == 'Pending':
            return 0
        done = 0
        pending = 0
        in_progress = 0
        for step in self.steps.all():
            if step.status in ['Succeeded','Failed','Cancelled']:
                done += 1
            elif step.status == 'Pending':
                pending += 1
            elif step.status == 'InProgress':
                in_progress += 1

        total = done + pending + in_progress
        progress = int(((done + (in_progress * .5)) * 100) / total)
        return progress

    def get_content_success(self):
        content = []

        if self.status != 'Succeeded':
            return content

        # Add content from the package and version
        version_content = self.version.get_content_success()
        if version_content:
            content.append(version_content)
   
        # Add content from dependent packages and versions
        packages = []
        for step in self.steps.filter(status = 'Succeeded').exclude(action = 'skip'):
            if step.package.id in packages:
                continue
            packages.append(step.package.id)
            step_content = step.version.get_content_success()
            if step_content:
                content.append(step_content)
        
        return content
    
    def get_content_failure(self):
        content = []

        if self.status != 'Failed':
            return content

        # Add content from the package and version
        version_content = self.version.get_content_failure()
        if version_content:
            content.append(version_content)
   
        # Add content from dependent packages and versions
        packages = []
        packages.append(self.package.id)
        for step in self.steps.filter(status = 'Failed').exclude(action = 'skip'):
            if step.package.id in packages:
                continue
            packages.append(step.package.id)
            step_content = step.version.get_content_failure()
            if step_content:
                content.append(step_content)
        
        return content

    def get_status_from_steps(self):
        pass

class PackageInstallationSession(models.Model):
    installation = models.ForeignKey(PackageInstallation, related_name='sessions')
    oauth = models.TextField()
    org_packages = models.TextField()
    metadata = models.TextField()

class PackageInstallationStep(models.Model):
    installation = models.ForeignKey(PackageInstallation, related_name='steps')
    package = models.ForeignKey(Package, related_name='installation_steps', null=True, blank=True)
    version = models.ForeignKey(PackageVersion, related_name='installation_steps', null=True, blank=True)
    previous_version = models.CharField(max_length=255, null=True, blank=True)
    action = models.CharField(max_length=32)
    status = models.CharField(max_length=32)
    log = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    order = models.IntegerField()

    class Meta:
        ordering = ['order',]

    def __unicode__(self):
        return '%s %s' % (self.action, self.version)

from mpinstaller.handlers import *
