from rest_framework import serializers
from mpinstaller.models import MetadataCondition
from mpinstaller.models import Package
from mpinstaller.models import PackageVersion
from mpinstaller.models import PackageVersionDependency
from mpinstaller.models import PackageInstallation
from mpinstaller.models import PackageInstallationStep

class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = ('id', 'namespace','name','description','current_prod','current_beta')

class MetadataConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetadataCondition
        fields = ('id','metadata_type','field','search','exclude_namespaces','method','no_match')

class RequiredPackageVersionSerializer(serializers.ModelSerializer):
    package = PackageSerializer()
    content_intro = serializers.Field(source='get_content_intro')
    is_beta = serializers.Field(source='is_beta')
    class Meta:
        model = PackageVersion
        fields = ('id','name','number','zip_url','is_beta','package','conditions','content_intro')

class PackageVersionDependencySerializer(serializers.ModelSerializer):
    requires = RequiredPackageVersionSerializer()
    class Meta:
        model = PackageVersionDependency
        fields = ('id','requires','order')

class PackageVersionSerializer(serializers.ModelSerializer):
    package = PackageSerializer()
    conditions = MetadataConditionSerializer(many=True)
    dependencies = PackageVersionDependencySerializer(many=True)
    is_beta = serializers.Field(source='is_beta')
    class Meta:
        model = PackageVersion
        fields = ('id','name','number','zip_url','is_beta', 'package', 'conditions','dependencies')

class InstallationStepSerializer(serializers.ModelSerializer):
    version = RequiredPackageVersionSerializer()
    progress = serializers.Field(source='get_progress')
    class Meta:
        model = PackageInstallationStep
        fields = ('id', 'version', 'previous_version', 'action', 'status', 'progress', 'log', 'created', 'modified','order')

class InstallationSerializer(serializers.ModelSerializer):
    version = PackageVersionSerializer()
    steps = InstallationStepSerializer(many=True)
    content_success = serializers.Field(source="get_content_success") 
    content_failure = serializers.Field(source="get_content_failure")
    progress = serializers.Field(source='get_progress')
    class Meta:
        model = PackageInstallation
        fields = ('id', 'org_type', 'status', 'log', 'created', 'modified', 'version', 'progress', 'steps', 'content_success', 'content_failure')
