from rest_framework import routers

from users.api_views import UserRoleViewSet, UserViewSet

router = routers.DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("user_roles", UserRoleViewSet, basename="user_roles")

urlpatterns = router.urls
