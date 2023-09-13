from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.http import HttpResponse
from rest_framework import permissions, views
from rest_framework.parsers import MultiPartParser
from users.serializers import LoginSerializer
from users.services import JWTHandler

from overschool import settings

jwt_handler = JWTHandler()


class LoginView(LoggingMixin, WithHeadersViewSet, views.APIView):
    """<h2>/api/login/</h2>\n"""

    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    parser_classes = (MultiPartParser,)

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        access_token = jwt_handler.create_access_token(subject=user.id)
        refresh_token = jwt_handler.create_refresh_token(subject=user.id)

        response = HttpResponse("/api/user/", status=200)
        development_mode_header = request.META.get("HTTP_X_DEVELOPMENT_MODE")
        if development_mode_header and development_mode_header == "false":
            SESSION_COOKIE_DOMAIN = ".overschool.by"
            response.set_cookie(
                key=settings.ACCESS,
                value=access_token,
                max_age=settings.COOKIE_EXPIRE_SECONDS,
                expires=settings.COOKIE_EXPIRE_SECONDS,
                httponly=True,
                samesite=None,
                secure=False,
                domain=SESSION_COOKIE_DOMAIN,
            )

            response.set_cookie(
                key=settings.REFRESH,
                value=refresh_token,
                max_age=settings.COOKIE_EXPIRE_SECONDS,
                expires=settings.COOKIE_EXPIRE_SECONDS,
                httponly=True,
                samesite=None,
                secure=False,
                domain=SESSION_COOKIE_DOMAIN,
            )
        else:
            response.set_cookie(
                key=settings.ACCESS,
                value=access_token,
                max_age=settings.COOKIE_EXPIRE_SECONDS,
                expires=settings.COOKIE_EXPIRE_SECONDS,
                httponly=True,
                samesite=None,
                secure=False,
            )

            response.set_cookie(
                key=settings.REFRESH,
                value=refresh_token,
                max_age=settings.COOKIE_EXPIRE_SECONDS,
                expires=settings.COOKIE_EXPIRE_SECONDS,
                httponly=True,
                samesite=None,
                secure=False,
            )

        return response
