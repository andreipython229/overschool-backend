from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.views import View

from overschool import settings


class LogoutView(View):
    def get(self, request):
        logout(request)
        response = HttpResponseRedirect("/api/")
        response.delete_cookie(settings.ACCESS)
        response.delete_cookie(settings.REFRESH)
        return response
