from common_services.mixins import WithHeadersViewSet, LoggingMixin
from courses.models import Course
from courses.serializers import CourseSerializer, CourseStudentsSerializer
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.models import User
from django.db.models.expressions import Window
from django.db.models import F, Max, Q, Sum, Avg, Count
from homeworks.paginators import UserHomeworkPagination
from lesson_tests.models import UserTest
from courses.models import StudentsGroup



class CourseViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated,)


class UsersCourse(LoggingMixin, WithHeadersViewSet, generics.ListAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    pagination_class = UserHomeworkPagination
    serializer_class = CourseStudentsSerializer

    def list(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            queryset = self.get_queryset(**serializer.data)
            paginator = self.pagination_class()
            data = paginator.paginate_queryset(request=request, queryset=queryset)
            return paginator.get_paginated_response(data=data)
        else:
            return Response(data=serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self, *args, **kwargs):
        queryset = StudentsGroup.objects.filter(
            course_id=kwargs['course_id']
        )
        check = queryset.values(email=F("students__email"),
                                student_name=F("students__first_name"),
                                student=F("students__user_id"),
                                group=F("group_id")).annotate(
            marks_sum=Sum("students__user_homeworks__mark"),
            average_mark=Avg("students__user_homeworks__mark"),
            progress=(F("students__user_progresses__lesson__order") * 100) / Count(
                "course_id__sections__lessons__lesson_id")
        )
        for c in check:
            c['marks_sum'] += sum([i.success_percent // 10 for i in UserTest.objects.filter(user=c['student'])])
        return check
