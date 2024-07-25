from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.db.models import (
    BooleanField,
    Case,
    ExpressionWrapper,
    OuterRef,
    Subquery,
    Value,
    When,
)
from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.response import Response
from schools.models import School
from schools.serializers import SchoolSerializer
from users.models import UserGroup


class UserSchoolsView(LoggingMixin, WithHeadersViewSet, generics.GenericAPIView):
    """Ендпоинт получения доступных школ\n
    <h2>/api/user-school/</h2>\n
    Ендпоинт получения названий школ, доступных
    пользователю"""

    serializer_class = SchoolSerializer

    def get_queryset(self):
        return School.objects.filter(groups__user=self.request.user).distinct()

    def list(self, request, *args, **kwargs):
        if self.request.user.is_anonymous:
            return HttpResponse(status=401)
        user_schools = self.get_queryset()
        if user_schools.first():
            user_group = UserGroup.objects.filter(
                user=self.request.user, school=OuterRef("pk")
            )
            user_schools = user_schools.annotate(
                role=Subquery(user_group.values("group__name")[:1])
            ).annotate(
                is_owner=Case(
                    When(owner=self.request.user, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                ),
                tariff_paid=Case(
                    When(tariff=None, then=Value(False)),
                    default=Value(True),
                    output_field=BooleanField(),
                ),
            )
            data = user_schools.values(
                "school_id",
                "name",
                "header_school",
                "role",
                "is_owner",
                "tariff_paid",
                "contact_link",
                "test_course",
            )
            return Response(data)
        else:
            data = []
            return Response(data, status=status.HTTP_200_OK)
