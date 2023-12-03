from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.contrib.auth import logout
from django.http import HttpResponse
from django.views import View
from rest_framework import permissions, serializers

from overschool import settings


class EmptySerializer(serializers.Serializer):
    pass


class LogoutView(LoggingMixin, WithHeadersViewSet, View):
    """<h2>/api/logout/</h2>\n"""

    permission_classes = [permissions.AllowAny]
    serializer_class = EmptySerializer

    def get(self, request):
        logout(request)
        development_mode_header = request.META.get("HTTP_X_DEVELOPMENT_MODE")
        if development_mode_header and development_mode_header == "false":
            SESSION_COOKIE_DOMAIN = settings.SESSION_COOKIE_DOMAIN
            response = HttpResponse(status=200)
            response.delete_cookie(settings.ACCESS, domain=SESSION_COOKIE_DOMAIN)
            response.delete_cookie(settings.REFRESH, domain=SESSION_COOKIE_DOMAIN)
            return response
        else:
            response = HttpResponse(status=200)
            response.delete_cookie(settings.ACCESS)
            response.delete_cookie(settings.REFRESH)
            return response
