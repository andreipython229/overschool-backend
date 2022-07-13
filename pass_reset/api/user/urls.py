
from .apis import ChangePasswordView

from django.urls import path, include

from . import apis

urlpatterns = [
    path("register/", apis.RegisterApi.as_view(), name="register"),
    path("login/", apis.LoginApi.as_view(), name="login"),
    path("me/", apis.UserApi.as_view(), name="me"),
    path("logout/", apis.LogoutApi.as_view(), name="logout"),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset'))
]
