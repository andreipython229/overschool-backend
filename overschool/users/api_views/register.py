from dj_rest_auth.serializers import TokenSerializer, JWTSerializer
from django.conf import settings
from django.contrib.auth import get_user_model

from dj_rest_auth.registration.views import RegisterView as _RegisterView


class RegisterView(_RegisterView):
    queryset = get_user_model().objects.all()

    def get_response_data(self, user):
        if getattr(settings, 'REST_USE_JWT', False):
            data = {
                'user': user,
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
            }
            print(user)
            return JWTSerializer(data, context=self.get_serializer_context()).data
        elif getattr(settings, 'REST_SESSION_LOGIN', False):
            return None
        else:
            return TokenSerializer(user.auth_token, context=self.get_serializer_context()).data
