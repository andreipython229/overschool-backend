from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.contrib.auth import login
from rest_framework import permissions, status, views
from rest_framework.authentication import SessionAuthentication
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from users.serializers import LoginSerializer


class LoginView(WithHeadersViewSet, views.APIView):
    """<h2>/api/login/</h2>\n"""

    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    parser_classes = (MultiPartParser,)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        login(request, user)

        tokens = serializer.create(serializer.validated_data)

        return Response(tokens)


class SocialLoginCompleteView(views.APIView):
    """
    Эндпоинт, проверяет сессию, установленную allauth, и выдает JWT.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        return Response(
            {
                "access": access_token,
                "refresh": refresh_token,
                "user": {
                    "id": user.pk,
                    "email": user.email,
                },
            },
            status=status.HTTP_200_OK,
        )
