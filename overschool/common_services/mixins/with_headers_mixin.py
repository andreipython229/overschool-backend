from rest_framework import viewsets


class WithHeadersViewSet(viewsets.GenericViewSet):
    @property
    def default_response_headers(self):
        headers = super().default_response_headers
        headers["access-control-allow-credentials"] = "true"
        headers["Access-Control-Allow-Origin"] = "*"
        return headers
