from common_services.mixins import WithHeadersViewSet
from django.contrib.auth import logout
from django.http import HttpResponse
from django.views import View
from rest_framework import permissions
from rest_framework import serializers
from overschool import settings


class EmptySerializer(serializers.Serializer):
    pass


class LogoutView(WithHeadersViewSet, View):
    permission_classes = [permissions.AllowAny]
    serializer_class = EmptySerializer

    def get(self, request):
        logout(request)
        response = HttpResponse(status=200)
        response.delete_cookie(settings.ACCESS)
        response.delete_cookie(settings.REFRESH)
        return response
