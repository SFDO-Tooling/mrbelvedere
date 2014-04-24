from rest_framework import viewsets
from mpinstaller.serializers import InstallationSerializer
from mpinstaller.serializers import PackageVersionContentSerializer
from mpinstaller.models import PackageInstallation
from mpinstaller.models import PackageVersion

class InstallationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Provides a detailed status of an installation and all its steps
    """
    queryset = PackageInstallation.objects.all()
    serializer_class = InstallationSerializer

class PackageVersionContentViewSet(viewsets.ModelViewSet):
    """
    Provides a single interface to all content fields related to a particular package version
    """
    queryset = PackageVersion.objects.all()
    serializer_class = PackageVersionContentSerializer
