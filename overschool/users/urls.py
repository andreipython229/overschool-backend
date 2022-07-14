from rest_framework import routers

from users.api_views import SchoolUserOfflineViewSet, SchoolUserViewSet

router = routers.DefaultRouter()
router.register("users", SchoolUserViewSet, basename="users")
router.register("users_offline/", SchoolUserOfflineViewSet, basename="users_offline")

urlpatterns = router.urls
