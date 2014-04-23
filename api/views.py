from rest_framework import viewsets
from mpinstaller.serializers import InstallationSerializer
from mpinstaller.models import PackageInstallation

class InstallationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = PackageInstallation.objects.all()
    serializer_class = InstallationSerializer
