from django.conf.urls import patterns, url, include
from api import views
from rest_framework.routers import DefaultRouter

# Create a router and register our viewsets with it.
router = DefaultRouter()
#router.register(r'packages', views.PackagesViewSet)
#router.register(r'package_versions', views.PackageVersionsViewSet)
#router.register(r'package_version_dependencies', views.PackageVersionDependenciesViewSet)
router.register(r'installations', views.InstallationViewSet)
router.register(r'version-content', views.PackageVersionContentViewSet)

# The API URLs are now determined automatically by the router.
# Additionally, we include the login URLs for the browseable API.
urlpatterns = patterns('',
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
)
