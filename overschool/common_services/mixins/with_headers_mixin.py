from django.conf import settings
from rest_framework import permissions, viewsets


class WithHeadersViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]

    @property
    def default_response_headers(self):
        headers = super().default_response_headers
        origin = self.request.headers.get("Origin")

        # Проверяем, что origin в списке разрешенных
        if origin in settings.CORS_ALLOWED_ORIGINS:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
            headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        return headers
