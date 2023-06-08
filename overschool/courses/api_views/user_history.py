from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import UserHomework
from courses.paginators import UserHomeworkPagination
from courses.serializers import HomeworkHistorySerializer
from django.db.models import F
from django.db.models import Subquery, OuterRef
from rest_framework import generics, permissions, status
from rest_framework.response import Response


class UserHistoryViewSet(LoggingMixin, WithHeadersViewSet, generics.ListAPIView):
    serializer_class = HomeworkHistorySerializer
    queryset = UserHomework.objects.all()
    permission_classes = [permissions.AllowAny]
    pagination_class = UserHomeworkPagination

    def get_queryset(self, *args, **kwargs):
        last_check_subquery = UserHomework.objects.filter(user=OuterRef('user')).order_by('-created_at')
        last_check = last_check_subquery.values('status', 'created_at', 'teacher__profile__avatar',
                                                'teacher__first_name', 'teacher__last_name', )[:1]

        queryset = UserHomework.objects.annotate(
            last_check_status=Subquery(last_check.values('status')),
            last_check_time=Subquery(last_check.values('created_at')),
            last_check_teacher_avatar=Subquery(last_check.values('teacher__profile__avatar')),
            last_check_teacher_name=Subquery(last_check.values('teacher__first_name')),
            last_check_teacher_lastname=Subquery(last_check.values('teacher__last_name')),
            last_check_teacher_massage=Subquery(last_check.values('user__user_homeworks__teacher_message')),
        ).values(
            "homework__name",
            "status",
            'text',
            last_check_status=F("last_check_status"),
            last_check_teacher_massege=F("last_check_teacher_massage"),
            last_check_time=F("last_check_time"),
            last_check_teacher_avatar=F("last_check_teacher_avatar"),
            last_check_teacher_name=F("last_check_teacher_name"),
            last_check_teacher_lastname=F("last_check_teacher_lastname"),
            student_avatar=F("user__profile__avatar"),
            student_name=F("user__first_name"),
            student_lastname=F("user__last_name"),
            student_response=F("user__user_homeworks__text"),
            student_response_time=F("created_at"),
            student_response_status=F("user__user_homeworks__status"),
            audio=F("user__user_homeworks__audio_files"),
            files_text=F("user__user_homeworks__text_files")
        )

        return queryset

    def list(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            queryset = self.get_queryset(**serializer.data)
            paginator = self.pagination_class()
            data = paginator.paginate_queryset(request=request, queryset=queryset)
            return paginator.get_paginated_response(data=data)
        else:
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
