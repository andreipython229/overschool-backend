from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import UserHomework
from courses.paginators import UserHomeworkPagination
from courses.serializers import UserHomeworkStatisticsSerializer
from django.db.models import F
from rest_framework import generics, permissions, status
from rest_framework.response import Response


class UserHistoryViewSet(LoggingMixin, WithHeadersViewSet, generics.ListAPIView):
    serializer_class = UserHomeworkStatisticsSerializer
    queryset = UserHomework.objects.all()
    permission_classes = [permissions.AllowAny]
    pagination_class = UserHomeworkPagination

    def get_queryset(self, *args, **kwargs):
        queryset = UserHomework.objects.all()

        return queryset.values(
            "mark",
            "status",
            check_homework_id=F("user__user_homeworks"),
            avatar=F("user__profile__avatar"),
            user_name=F("user__first_name"),
            user_lastname=F("user__last_name"),
            homework_name=F("homework__name"),
            status_history=F("user__user_homeworks__status"),
            send_homework_id=F("user__user_homeworks__homework_id")
        )

    def list(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            queryset = self.get_queryset(**serializer.data)
            paginator = self.pagination_class()
            data = paginator.paginate_queryset(request=request, queryset=queryset)
            return paginator.get_paginated_response(data=data)
        else:
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
