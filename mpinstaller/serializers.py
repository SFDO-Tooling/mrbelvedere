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
    class Meta:
        model = PackageVersion
        fields = ('id','name','number','zip_url','conditions','package')

class PackageVersionDependencySerializer(serializers.ModelSerializer):
    requires = RequiredPackageVersionSerializer()
    class Meta:
        model = PackageVersionDependency
        fields = ('id','requires','order')

class PackageVersionSerializer(serializers.ModelSerializer):
    package = PackageSerializer()
    conditions = MetadataConditionSerializer(many=True)
    dependencies = PackageVersionDependencySerializer(many=True)
    class Meta:
        model = PackageVersion
        fields = ('id','name','number','zip_url','conditions','package','dependencies')

class InstallationStepSerializer(serializers.ModelSerializer):
    version = RequiredPackageVersionSerializer()
    class Meta:
        model = PackageInstallationStep
        fields = ('id', 'version', 'previous_version', 'action', 'status', 'log', 'created', 'modified','order')

class InstallationSerializer(serializers.ModelSerializer):
    version = PackageVersionSerializer()
    steps = InstallationStepSerializer(many=True)
    class Meta:
        model = PackageInstallation
        fields = ('id', 'org_type', 'status', 'log', 'created', 'modified', 'version', 'steps')
