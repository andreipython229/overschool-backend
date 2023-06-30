from common_services.mixins import WithHeadersViewSet
from django.http import HttpResponse
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from schools.models import School
from schools.serializers import SchoolSerializer


class UserSchoolsView(WithHeadersViewSet, generics.GenericAPIView):
    """Ендпоинт получения доступных школ\n
    Ендпоинт получения названий школ, доступных
    пользователю"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SchoolSerializer

    def get_queryset(self):
        return School.objects.filter(groups__user=self.request.user).distinct()

    def list(self, request, *args, **kwargs):
        user_schools = self.get_queryset()
        if user_schools.first():
            data = user_schools.values("name")
            return Response(data)
        else:
            return Response(
                "У пользователя нет доступа ни к одной школе",
                status=status.HTTP_204_NO_CONTENT,
            )
