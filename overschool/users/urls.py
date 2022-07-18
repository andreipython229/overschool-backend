from rest_framework import routers
from users.api_views import SchoolUserViewSet

router = routers.DefaultRouter()
router.register("users", SchoolUserViewSet, basename="users")

urlpatterns = router.urls
