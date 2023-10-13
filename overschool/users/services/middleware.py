from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin
from jwt import InvalidTokenError, decode

User = get_user_model()

from users.services import JWTHandler

jwt_handler = JWTHandler()


class AuthOptionalMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        access_token = request.COOKIES.get(settings.ACCESS)
        refresh_token = request.COOKIES.get(settings.REFRESH)
        if not (access_token and refresh_token):
            request.user = None
            return None
        try:
            payload = decode(
                access_token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            user = User.objects.get(pk=payload.get("sub"))
            request.user = user
        except InvalidTokenError:
            try:
                payload = decode(
                    refresh_token,
                    settings.JWT_REFRESH_SECRET_KEY,
                    algorithms=[settings.ALGORITHM],
                )
                user = User.objects.get(pk=payload.get("sub"))
                request.user = user
                # Refresh access token here
                new_access_token = jwt_handler.create_access_token(user.id)
                request.COOKIES[settings.ACCESS] = new_access_token
                response = HttpResponseRedirect(request.path_info)
                response.delete_cookie(settings.ACCESS)
                response.delete_cookie(settings.REFRESH)
                response.set_cookie(
                    key=settings.ACCESS,
                    value=new_access_token,
                    max_age=settings.COOKIE_EXPIRE_SECONDS,
                    expires=settings.COOKIE_EXPIRE_SECONDS,
                    httponly=True,
                    samesite=None,
                    secure=False,
                )
                return response
            except:
                request.user = None
        return None
