from rest_framework import routers
from users.api_views import (
    ConfidentFilesViewSet,
    ProfileViewSet,
    UserViewSet,
)

router = routers.DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("profiles", ProfileViewSet, basename="profiles")
router.register("upload", ConfidentFilesViewSet, basename="upload")

urlpatterns = router.urls

