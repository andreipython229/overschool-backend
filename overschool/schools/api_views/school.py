from common_services.mixins import LoggingMixin, WithHeadersViewSet
from schools.models import School
from schools.serializers import SchoolSerializer
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from django.db.models import Avg, Count, F, Sum
from courses.models import StudentsGroup

from lesson_tests.models import UserTest
from rest_framework.response import Response


class SchoolViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True)
    def stats(self, request, pk):
        """ Статистика учеников школы"""
        queryset = StudentsGroup.objects.all()
        data = queryset.values(course=F("course_id"),
                               email=F("students__email"),
                               student_name=F("students__first_name"),
                               student=F("students__id"),
                               group=F("group_id"),
                               last_active=F("students__date_joined"),
                               update_date=F("students__date_joined"),
                               ending_date=F("students__date_joined")
                               ).annotate(
            mark_sum=Sum("students__user_homeworks__mark"),
            average_mark=Avg("students__user_homeworks__mark"),
            progress=(F("students__user_progresses__lesson__order") * 100)
                     / Count("course_id__sections__lessons__lesson_id"),
        )

        for row in data:
            mark_sum = (
                UserTest.objects.filter(user=row["student"])
                    .values("user")
                    .aggregate(mark_sum=Sum("success_percent"))["mark_sum"]
            )
            row["mark_sum"] += mark_sum // 10 if bool(mark_sum) else 0
        page = self.paginate_queryset(data)
        if page is not None:
            return self.get_paginated_response(page)
        return Response(data)
