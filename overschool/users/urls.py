from django.urls import path
from rest_framework import routers

from users.api_views import (
    LoginView,
    LogoutView,
    RegisterView,
    UserRoleViewSet,
    UserView,
    UserViewSet,
)

router = routers.DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("user_roles", UserRoleViewSet, basename="user_roles")

urlpatterns_to_add = [
    path("register", RegisterView.as_view(), name="register"),
    path("login", LoginView.as_view(), name="login"),
    path("user", UserView.as_view(), name="user"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("admin_register/", RegisterView.as_view(), name="register"),
]
urlpatterns = router.urls
urlpatterns += urlpatterns_to_add
