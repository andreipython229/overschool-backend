from django.contrib.auth import logout
from django.http import HttpResponse
from django.views import View
from common_services.mixins import WithHeadersViewSet
from overschool import settings


class LogoutView(WithHeadersViewSet, View):
    def get(self, request):
        logout(request)
        response = HttpResponse(status=200)
        response.delete_cookie(settings.ACCESS)
        response.delete_cookie(settings.REFRESH)
        return response
