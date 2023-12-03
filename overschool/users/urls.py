from rest_framework import routers
from users.api_views import ConfidentFilesViewSet, ProfileViewSet, UserViewSet


router = routers.DefaultRouter()
router.register("user", UserViewSet, basename="user")
router.register("profile", ProfileViewSet, basename="profile")
router.register("upload", ConfidentFilesViewSet, basename="upload")

urlpatterns = router.urls
