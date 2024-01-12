from rest_framework import routers
from users.api_views import ProfileViewSet, UserViewSet

router = routers.DefaultRouter()
router.register("user", UserViewSet, basename="user")
router.register("profile", ProfileViewSet, basename="profile")

urlpatterns = router.urls
