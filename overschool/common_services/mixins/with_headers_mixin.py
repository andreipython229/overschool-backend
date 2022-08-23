from rest_framework import viewsets
from rest_framework import permissions

class WithHeadersViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]
    @property
    def default_response_headers(self):
        headers = super().default_response_headers
        headers["access-control-allow-credentials"] = "true"
        headers["Access-Control-Allow-Origin"] = "*"
        headers["Access-Control-Allow-Methods"] = "*"
        return headers
