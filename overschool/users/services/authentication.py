from django.contrib.auth import get_user_model
from jwt import InvalidTokenError, decode
from rest_framework.authentication import BaseAuthentication
from django.http import HttpResponseRedirect
from django.conf import settings

from users.services import JWTHandler

User = get_user_model()
jwt_handler = JWTHandler()


class CustomAuthentication(BaseAuthentication):
    def authenticate(self, request):
        access_token = request.COOKIES.get(settings.ACCESS)
        refresh_token = request.COOKIES.get(settings.REFRESH)

        if not (access_token and refresh_token):
            return None

        try:
            # Ваш код для декодирования access_token и получения пользователя
            payload = decode(
                access_token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            user = User.objects.get(pk=payload.get("sub"))
            request.user = user

            # Верните пользователь и его токены аутентификации
            return user, access_token

        except InvalidTokenError:
            try:
                # Ваш код для декодирования refresh_token и получения пользователя
                payload = decode(
                    refresh_token,
                    settings.JWT_REFRESH_SECRET_KEY,
                    algorithms=[settings.ALGORITHM],
                )
                user = User.objects.get(pk=payload.get("sub"))
                request.user = user

                # Обновите access_token
                new_access_token = jwt_handler.create_access_token(user.id)
                response = HttpResponseRedirect(request.path_info)
                response.set_cookie(
                    key=settings.ACCESS,
                    value=new_access_token,
                    max_age=settings.COOKIE_EXPIRE_SECONDS,
                    expires=settings.COOKIE_EXPIRE_SECONDS,
                    httponly=True,
                    samesite=None,
                    secure=False,
                )
                return user, new_access_token

            except:
                return None
