from rest_framework import viewsets


class WithHeadersViewSet(viewsets.ModelViewSet):
    @property
    def default_response_headers(self):
        headers = super().default_response_headers.fget(self)
        headers["access-control-allow-credentials"] = True
        headers["Access-Control-Allow-Origin"] = "*"
        return headers
