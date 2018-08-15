import hashlib
import os
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from mpinstaller.utils import obscure_salesforce_log
from tinymce.models import HTMLField

INSTALLATION_STATUS_CHOICES = (
    ('Pending','Pending'),
    ('InProgress', 'In Progress'),
    ('Succeeded', 'Succeeded'),
    ('Failed', 'Failed'),
)
INSTALLATION_STEP_STATUS_CHOICES = (
    ('Pending','Pending'),
    ('InProgress','In Progress'),
    ('Succeeded','Succeeded'),
    ('Failed','Failed'),
    ('Cancelled','Cancelled'),
)
INSTALLATION_ACTION_CHOICES = (
    ('install','Install'),
    ('upgrade','Upgrade'),
    ('uninstall','Uninstall'),
    ('skip','No change'),
)

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

class OrgAction(models.Model):
    slug = models.SlugField()
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    force_sandbox = models.BooleanField(default=False, help_text="If checked, production installs will be blocked unless the action has been successfully run against a sandbox of the production org.")
    content_intro = HTMLField(null=True, blank=True, help_text="Shown on the page to start an installation in the Action Information panel if provided.")
    content_success = HTMLField(null=True, blank=True, help_text="Shown on the installation status page after a successful installation in the Next Steps panel if provided.")
    content_failure = HTMLField(null=True, blank=True, help_text="Shown on the installation status page after a failed installation in the Next Steps panel if provided.")

class Package(models.Model):
    namespace = models.SlugField(max_length=128)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    current_prod = models.ForeignKey('mpinstaller.PackageVersion', related_name='current_prod', null=True, blank=True)
    current_beta = models.ForeignKey('mpinstaller.PackageVersion', related_name='current_beta', null=True, blank=True)
    current_github = models.ForeignKey('mpinstaller.PackageVersion', related_name='current_github', null=True, blank=True)
    key = models.CharField(max_length=255, null=True, blank=True)
    force_sandbox = models.BooleanField(default=False, help_text="If checked, production installs will be blocked unless a sandbox install of the same org for the same version was successful")
    content_intro = HTMLField(null=True, blank=True, help_text="Shown on the page to start an installation in the Package Information panel if provided.")
    content_success = HTMLField(null=True, blank=True, help_text="Shown on the installation status page after a successful installation in the Next Steps panel if provided.")
    content_failure = HTMLField(null=True, blank=True, help_text="Shown on the installation status page after a failed installation in the Next Steps panel if provided.")
    content_intro_beta = HTMLField(null=True, blank=True, help_text="Shown instead of Content intro if the package is a beta.")
    content_success_beta = HTMLField(null=True, blank=True, help_text="Shown instead of Content success if the package is a beta.")
    content_failure_beta = HTMLField(null=True, blank=True, help_text="Shown instead of Content failure if the package is a beta.")
    whitelist = models.ForeignKey('mpinstaller.WhiteList', related_name='packages', null=True, blank=True)

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
                'repo_url': version.requires.repo_url,
                'zip_url': version.requires.zip_url,
            })

        dependencies.append({
            'namespace': self.namespace,
            'number': parent.number,
            'repo_url': parent.repo_url,
            'zip_url': parent.zip_url,
        })
        return dependencies
        
    def update_dependencies(self, beta, dependencies):
        if beta: 
            parent = self.current_beta
        else:
            parent = self.current_prod

        # Handle changing parent first
        new_parent = None
        for dependency in dependencies:
            if dependency['namespace'] != self.namespace:
                # Skip everything but the parent namespace
                continue

            number = dependency.get('number',None)
            repo_url = dependency.get('repo_url',None)
            zip_url = dependency.get('zip_url',None)

            if number and parent.number != number:
                new_parent, created = PackageVersion.objects.get_or_create(
                    package = self,
                    number = number,
                    defaults = {'name': number},
                )

            elif zip_url and parent.zip_url != number:
                new_parent, created = PackageVersion.objects.get_or_create(
                    package = self,
                    zip_url = zip_url,
                    defaults = {'name': parent.name},
                )

        # If a new parent was created, copy over all the depedencies from the previous parent and set the new version as current
        if new_parent:
            for dependency in parent.dependencies.all():
            
                new_dependency, created = PackageVersionDependency.objects.get_or_create(
                    version = new_parent,
                    requires = dependency.requires,
                    defaults = {'order': dependency.order},
                )

            # Map any metadata conditions from the old parent
            for condition in parent.conditions.all():
                new_parent.conditions.add(condition)

            # Set the new parent as the current beta or prod version
            if beta:
                self.current_beta = new_parent
            else:
                self.current_prod = new_parent
            self.save()
            parent = new_parent

        versions = {}
        for dependency in parent.dependencies.all():
            versions[dependency.requires.package.namespace] = dependency

        # Loop through all the dependencies.  Create and link new versions as needed
        for dependency in dependencies:
            current_dependency = versions.get(dependency['namespace'])
            if not current_dependency:
                # We don't create new dependencies through this process, only update existing ones
                continue

            version = current_dependency.requires

            new_version = None

            number = dependency.get('number',None)
            if not number:
                zip_url = dependency.get('zip_url',None)
                if version.zip_url != zip_url:
                    # If the zip_url has changed, create a new PackageVersion if none exists with the zip url
                    new_version, created = PackageVersion.objects.get_or_create(
                        package = version.package,
                        zip_url = zip_url,
                        defaults = {'name': version.name},
                    )
            else:
                if version.number != number:
                    # If the version number has changed, create a new PackageVersion if none exists with the number
                    new_version, created = PackageVersion.objects.get_or_create(
                        package = version.package,
                        number = number,
                        defaults = {'name': version.number},
                    )

            if new_version:
                # Map any metadata conditions from the old version
                for condition in version.conditions.all():
                    new_version.conditions.add(condition)

                current_dependency.requires = new_version
                current_dependency.save()
                    
        return self.get_dependencies(beta)

    class Meta:
        ordering = ['namespace',]

class PackageVersion(models.Model):
    package = models.ForeignKey(Package, related_name='versions')
    name = models.CharField(max_length=255)
    number = models.CharField(max_length=32, null=True, blank=True)
    zip_url = models.URLField(null=True, blank=True)
    repo_url = models.URLField(null=True, blank=True)
    api_version = models.CharField(max_length=4, null=True, blank=True)
    github_username = models.CharField(max_length=255, null=True, blank=True)
    github_password = models.CharField(max_length=255, null=True, blank=True)
    branch = models.CharField(max_length=255, null=True, blank=True)
    subfolder = models.CharField(max_length=255, null=True, blank=True)
    namespace_token = models.CharField(max_length=255, null=True, blank=True, help_text="If provided, all files in the archive will be scanned and the token will be replaced with the namespace provided.  For CumulusCI, the default token is %%%NAMESPACE%%%")
    namespace = models.CharField(max_length=255, null=True, blank=True, help_text="If provided, the namespace_token will be replaced with this namespace.  If not provided, the token will be cleared.  Example: npsp")
    package_name = models.CharField(max_length=255, null=True, blank=True, help_text="If configuring a Github repository for contributions, enter the package name for unmanaged deployments here.  This is used to retrieve a contribution's packaged metadata from a Salesforce org.")
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

    def requires_beta(self):
        if self.is_beta():
            return True
        for dependency in self.dependencies.all():
            if dependency.requires.is_beta():
                return True
        return False

    def get_installer_url(self, request=None):
        redirect = None
        if self.package.current_prod and self.package.current_prod.id == self.id:
            redirect = '/mpinstaller/%s' %  self.package.namespace
        elif self.package.current_beta and self.package.current_beta.id == self.id:
            redirect = '/mpinstaller/%s/beta' %  self.package.namespace
        else:
            redirect = '/mpinstaller/%s/version/%s' %  (self.package.namespace, self.id)
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
            type_items = metadata[condition.metadata_type]
            if type_items is None:
                type_items = []
            for item in type_items:
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

        if self.is_beta():
            if self.package.content_intro_beta:
                content.append(self.package.content_intro_beta)
        if not content and self.package.content_intro:
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
    requires = models.ForeignKey(PackageVersion, related_name='required_by', null=True, blank=True)
    action = models.ForeignKey(OrgAction, related_name='required_by', null=True, blank=True)
    order = models.IntegerField()

    def __unicode__(self):
        if self.requires:
            return '%s (%s) requires %s (%s)' % (
                self.version.number,
                self.version.package.namespace,
                self.requires.number,
                self.requires.package.namespace,
            )
        else:
            return '%s (%s) requires action ' % (
                self.version.number,
                self.version.package.namespace,
                self.action.name,
            )

    class Meta:
        ordering = ['order',]

class WhiteList(models.Model):
    name = models.CharField(max_length=255)
    
    def __unicode__(self):
        return self.name

class WhiteListOrg(models.Model):
    name = models.CharField(max_length=255)
    whitelist = models.ForeignKey(WhiteList, related_name='orgs')
    org_id = models.CharField(max_length=18)

    def __unicode__(self):
        return '{} ({})'.format(self.name, self.org_id)

class PackageInstallation(models.Model):
    install_hash = models.CharField(max_length=128, default=lambda:hashlib.sha512(os.urandom(512)).hexdigest())
    package = models.ForeignKey(Package, related_name='installations')
    version = models.ForeignKey(PackageVersion, related_name='installations', null=True, blank=True)
    git_ref = models.CharField(max_length=255, null=True, blank=True)
    fork = models.CharField(max_length=255, null=True, blank=True)
    org_id = models.CharField(max_length=32)
    org_type = models.CharField(max_length=255)
    instance_url = models.CharField(max_length=255)
    status = models.CharField(choices=INSTALLATION_STATUS_CHOICES, max_length=32)
    username = models.CharField(max_length=255)
    install_map = models.TextField(null=True, blank=True)
    log = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created',]

    def __unicode__(self):
        return '%s: Install %s' % (self.id, self.version)

    def get_progress(self):
        if self.status in ['Succeeded','Failed','Cancelled']:
            return 100
        if self.status == 'Pending':
            return 0

        steps = 0
        steps_progress = 0
        for step in self.steps.all():
            steps += 1
            steps_progress += step.get_progress()

        if steps == 0:
            return 100

        progress = int(steps_progress / steps)
        return progress

    def get_content_success(self):
        content = []

        if self.status != 'Succeeded':
            return content

        # Add content from the package and version
        if self.version:
            version_content = self.version.get_content_success()
            if version_content:
                content.append(version_content)
   
        # Add content from dependent packages and versions
        packages = []
        packages.append(self.package.id)
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
        if self.version:
            version_content = self.version.get_content_failure()
            if version_content:
                content.append(version_content)
   
        # Add content from dependent packages and versions
        packages = []
        #packages.append(self.package.id)
        for step in self.steps.filter(status = 'Failed').exclude(action = 'skip'):
            if step.package.id in packages:
                continue
            packages.append(step.package.id)
            step_content = None
            if step.error.content:
                step_content = {'heading': step.package.name, 'body': step.error.content.resolution}
            else:
                step_content = step.version.get_content_failure()
            if step_content:
                content.append(step_content)
        
        return content

    def get_status_from_steps(self):
        pass

class InstallationErrorContent(models.Model):
    resolution = HTMLField()

class InstallationErrorManager(models.Manager):
    def drilldown(self, keyword=None, has_content=None, count_min=None, parent_package=None, parent_version=None, packages=None, versions=None, org_types=None, date_start=None, date_end=None):
        q_errors = self.filter(hide_from_report=False).order_by('message')

        if keyword is not None:
            q_errors = q_errors.filter(message__icontains = keyword)

        if has_content is not None:
            q_errors = q_errors.filter(content__isnull = not has_content)

        q_steps = self.drilldown_steps(parent_package=parent_package, parent_version=parent_version, packages=packages, versions=versions, org_types=org_types, date_start=date_start, date_end=date_end)
        q_steps = q_steps.filter(error__in = q_errors)    
        step_counts = q_steps.values('error').annotate(count=models.Count('id')).order_by()

        step_counts_dict = {}
        for step_count in step_counts:
            step_counts_dict[step_count['error']] = step_count['count']

        errors = []
 
        for error in q_errors:
            count = step_counts_dict.get(error.id, 0)
            if count_min is not None and count < count_min:
                continue
            errors.append({ 'error': error, 'count': count })

        facets = {
            'packages': q_steps.values('package', 'package__namespace').annotate(count=models.Count('id')).order_by(),
            'versions': q_steps.values('version', 'version__name', 'version__package__namespace').annotate(count=models.Count('id')).order_by(),
            'org_types': [{'org_type': row['installation__org_type'], 'count': row['count']} for row in q_steps.values('installation__org_type').annotate(count=models.Count('id')).order_by()],
            'date_start': q_steps.aggregate(models.Min('created'))['created__min'],
            'date_end': q_steps.aggregate(models.Max('created'))['created__max'],
        }

        return {'errors': errors, 'facets': facets}

    def drilldown_steps(self, parent_package=None, parent_version=None, packages=None, versions=None, org_types=None, date_start=None, date_end=None):
        q_steps = PackageInstallationStep.objects.all()

        if parent_package is not None:
            q_steps = q_steps.filter(installation__package = parent_package)

        if parent_version is not None:
            q_steps = q_steps.filter(installation__version = parent_version)

        if packages is not None:
            q_steps = q_steps.filter(package__in = packages)

        if versions is not None:
            q_steps = q_steps.filter(version__in = versions)

        if org_types is not None:
            q_steps = q_steps.filter(installation__org_type__in = org_types)

        if date_start:
            q_steps = q_steps.filter(created__gte = date_start)

        if date_end:
            q_steps = q_steps.filter(created__lte = date_end)

        return q_steps


class InstallationError(models.Model):
    message = models.TextField()
    content = models.ForeignKey(InstallationErrorContent, null=True, blank=True, related_name='errors')
    fallback_content = models.ForeignKey(InstallationErrorContent, null=True, blank=True, related_name='errors_fallback')
    hide_from_report = models.BooleanField(default=False)

    objects = InstallationErrorManager()
    
class PackageInstallationSession(models.Model):
    installation = models.ForeignKey(PackageInstallation, related_name='sessions')
    oauth = models.TextField()
    org_packages = models.TextField()
    metadata = models.TextField()

class PackageInstallationStep(models.Model):
    installation = models.ForeignKey(PackageInstallation, related_name='steps')
    package = models.ForeignKey(Package, related_name='installation_steps', null=True, blank=True)
    version = models.ForeignKey(PackageVersion, related_name='installation_steps', null=True, blank=True)
    action = models.ForeignKey(OrgAction, related_name='installation_steps', null=True, blank=True)
    previous_version = models.CharField(max_length=255, null=True, blank=True)
    action = models.CharField(choices=INSTALLATION_ACTION_CHOICES, max_length=32)
    status = models.CharField(choices=INSTALLATION_STEP_STATUS_CHOICES, max_length=32)
    log = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    order = models.IntegerField()
    error = models.ForeignKey(InstallationError, null=True, blank=True, related_name='steps')

    def get_progress(self):
        if self.status == 'Pending':
            return 0
        if self.status == 'InProgress':
            return 50
        if self.status in ['Cancelled', 'Failed', 'Succeeded']:
            return 100

        return 100

    def set_error(self):
        if not self.log:
            return
        obscurred_log = obscure_salesforce_log(self.log)
        error, created = InstallationError.objects.get_or_create(message = obscurred_log)
        self.error = error
        self.log = obscurred_log
        self.save()

    class Meta:
        ordering = ['-installation__id', 'order',]

    def __unicode__(self):
        return '%s %s' % (self.action, self.version)

EDIT_PICKLIST_ACTION_CHOICES = (
    ('insert', 'Insert if not existing'),
    ('upsert', 'Upsert'),
    ('delete', 'Delete'),
)

class BaseActionEditPicklist(models.Model):
    action = models.CharField(choices=EDIT_PICKLIST_ACTION_CHOICES, max_length=16)
    custom_object = models.CharField(max_length=255)
    custom_field = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    default = models.BooleanField()

    class Meta:
        abstract = True

class ActionEditPicklist(OrgAction, BaseActionEditPicklist):
    class Meta:
        pass

STAGE_FORECAST_CATEGORY_CHOICES = (
    ('Best Case', 'Best Case'),
    ('Closed', 'Closed'),
    ('Commit', 'Commit'),
    ('Omitted', 'Omitted'),
    ('Pipeline', 'Pipeline'),
)

def validate_probability(value):
    if int(value) > 100:
        raise ValidationError('Probability cannot be greater than 100')
    if int(value) < 0:
        raise ValidationError('Probability cannot be less than 100')

class ActionEditStageName(OrgAction, BaseActionEditPicklist):
    closed = models.BooleanField()
    won = models.BooleanField()
    probability = models.IntegerField(validators=[validate_probability])
    forecast_category = models.CharField(max_length=16, choices=STAGE_FORECAST_CATEGORY_CHOICES)
