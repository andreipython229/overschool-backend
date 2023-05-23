from django.http import HttpResponse
from rest_framework import permissions, views
from users.serializers import LoginSerializer
from users.services import JWTHandler
from common_services.mixins import WithHeadersViewSet
from overschool import settings

jwt_handler = JWTHandler()


class LoginView(WithHeadersViewSet, views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        access_token = jwt_handler.create_access_token(subject=user.id)
        refresh_token = jwt_handler.create_refresh_token(subject=user.id)

        response = HttpResponse("http://127.0.0.1:8000/api/users/", status=200)
        response.set_cookie(
            key=settings.ACCESS,
            value=access_token,
            max_age=settings.COOKIE_EXPIRE_SECONDS,
            expires=settings.COOKIE_EXPIRE_SECONDS,
            httponly=True,
        )
        response.set_cookie(
            key=settings.REFRESH,
            value=refresh_token,
            max_age=settings.COOKIE_EXPIRE_SECONDS,
            expires=settings.COOKIE_EXPIRE_SECONDS,
            httponly=True,
        )
        return response
