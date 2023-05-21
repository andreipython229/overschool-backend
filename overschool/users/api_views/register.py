from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from rest_framework import generics, permissions
from users.serializers import SignupSerializer
from users.services import JWTHandler

from overschool import settings

User = get_user_model()
jwt_handler = JWTHandler()


class SignupView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SignupSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response = HttpResponseRedirect("/api/login/")
        response.set_cookie(
            key=settings.ACCESS,
            value="access_token_value",
            max_age=settings.COOKIE_EXPIRE_SECONDS,
            expires=settings.COOKIE_EXPIRE_SECONDS,
            httponly=True,
        )
        response.set_cookie(
            key=settings.REFRESH,
            value="refresh_token_value",
            max_age=settings.COOKIE_EXPIRE_SECONDS,
            expires=settings.COOKIE_EXPIRE_SECONDS,
            httponly=True,
        )
        return response
