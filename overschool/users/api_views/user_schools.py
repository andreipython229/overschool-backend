from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.db.models import OuterRef, Subquery
from django.http import HttpResponse
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from schools.models import School
from schools.serializers import SchoolSerializer
from users.models import UserGroup


class UserSchoolsView(LoggingMixin, WithHeadersViewSet, generics.GenericAPIView):
    """Ендпоинт получения доступных школ\n
    <h2>/api/user-school/</h2>\n
    Ендпоинт получения названий школ, доступных
    пользователю"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SchoolSerializer

    def get_queryset(self):
        return School.objects.filter(groups__user=self.request.user).distinct()

    def list(self, request, *args, **kwargs):
        user_schools = self.get_queryset()
        if user_schools.first():
            user_group = UserGroup.objects.filter(
                user=self.request.user, school=OuterRef("pk")
            )
            user_schools = user_schools.annotate(
                role=Subquery(user_group.values("group__name")[:1])
            )
            data = user_schools.values("school_id", "name", "header_school", "role")
            return Response(data)
        else:
            return Response(
                "У пользователя нет доступа ни к одной школе",
                status=status.HTTP_204_NO_CONTENT,
            )
