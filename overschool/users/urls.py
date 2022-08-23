from rest_framework import routers
from django.urls import path
from users.api_views import (
    ConfidentFilesViewSet,
    ProfileViewSet,
    UserViewSet,
    RegisterView,
    LoginView
)

router = routers.DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("register_user", RegisterView, basename="register_user")
router.register("login_user", LoginView, basename="login_user")
router.register("profiles", ProfileViewSet, basename="profiles")
router.register("upload", ConfidentFilesViewSet, basename="upload")

urlpatterns = router.urls

