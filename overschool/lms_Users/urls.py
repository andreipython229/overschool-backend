from django.urls import path, include
from rest_framework import routers
from lms_Users.api.views import UserViewSet

router = routers.DefaultRouter()
router.register('users', UserViewSet, basename="users")

urlpatterns = router.urls