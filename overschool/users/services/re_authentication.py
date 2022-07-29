import jwt
from django.conf import settings
from rest_framework import authentication, exceptions

from users.models import User


class CustomUserReAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        token = request.COOKIES.get("jwt")

        if not token:
            return None

        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        except:
            raise exceptions.AuthenticationFailed("Unauthorized")

        user = User.objects.filter(id=payload["id"]).first()

        return (user, None)
