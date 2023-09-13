from rest_framework import routers
from users.api_views import ConfidentFilesViewSet, ProfileViewSet, UserViewSet, AllUsersViewSet


router = routers.DefaultRouter()
router.register("user", UserViewSet, basename="user")
router.register("all_users", AllUsersViewSet, basename="all-users")
router.register("profile", ProfileViewSet, basename="profile")
router.register("upload", ConfidentFilesViewSet, basename="upload")

urlpatterns = router.urls
