from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.contrib.auth import logout
from django.views import View
from rest_framework import permissions, serializers, status
from rest_framework.response import Response


class EmptySerializer(serializers.Serializer):
    pass


class LogoutView(LoggingMixin, WithHeadersViewSet, View):
    """<h2>/api/logout/</h2>\n"""

    permission_classes = [permissions.AllowAny]
    serializer_class = EmptySerializer

    def get(self, request):
        logout(request)
        return Response({"detail": "Успешный выход из системы"}, status=200)
