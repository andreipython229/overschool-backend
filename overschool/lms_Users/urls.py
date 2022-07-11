from rest_framework import routers
from lms_Users.api_views import UserViewSet

router = routers.DefaultRouter()
router.register('users', UserViewSet, basename="users")

urlpatterns = router.urls