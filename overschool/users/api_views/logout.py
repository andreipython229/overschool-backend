from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.views import View
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)


class LogoutView(LoggingMixin, WithHeadersViewSet, View):
    """<h2>/api/logout/</h2>\n"""

    permission_classes = [permissions.AllowAny]
    serializer_class = LogoutSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data["refresh_token"]
        try:
            # Отправляет RefreshToken в блэклист, если он присутствует
            RefreshToken(refresh_token).blacklist()

            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Failed to logout: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
