from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.db.models import F, Max, Q
from django.db.models.expressions import Window
from homeworks.models import UserHomework
from homeworks.paginators import UserHomeworkPagination
from homeworks.serializers import (
    UserHomeworkSerializer,
    UserHomeworkStatisticsSerializer,
)
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response


class HomeworkViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = UserHomework.objects.all()
    serializer_class = UserHomeworkSerializer
    permission_classes = [permissions.DjangoModelPermissions]


class HomeworkStatisticsView(LoggingMixin, WithHeadersViewSet, generics.ListAPIView):
    serializer_class = UserHomeworkStatisticsSerializer
    queryset = UserHomework.objects.all()
    permission_classes = [permissions.AllowAny]
    pagination_class = UserHomeworkPagination

    def list(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            queryset = self.get_queryset(**serializer.data)
            paginator = self.pagination_class()
            data = paginator.paginate_queryset(request=request, queryset=queryset)
            return paginator.get_paginated_response(data=data)
        else:
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self, *args, **kwargs):
        queryset = UserHomework.objects.filter(
            Q(updated_at__gte=kwargs["start_date"]) & Q(updated_at__lte=kwargs["end_date"])
        )
        try:
            queryset = queryset.filter(Q(mark__gte=kwargs["start_mark"]) & Q(mark__lte=kwargs["end_mark"]))
        except KeyError:
            pass
        if kwargs["status"]:
            queryset = queryset.filter(status=kwargs["status"])
        if kwargs["homework_id"]:
            queryset = queryset.filter(homework_id__in=kwargs["homework_id"])
        if kwargs["course_id"]:
            queryset = queryset.filter(homework__lesson__section__course__id=kwargs["course_id"])
        if kwargs["group_id"]:
            queryset = queryset.filter(user__pk=kwargs["group_id"])
        return queryset.values(
            "mark",
            "status",
            user_homework=F("homework_id"),
            email=F("user__email"),
            avatar=F("user__profile__avatar"),
            homework_name=F("homework__section__course__name"),
            homework_pk=F("homework__homework_id"),
            lesson_name=F("homework__name"),
            last_update=Window(
                expression=Max("updated_at"), partition_by=[F("user__email"), F("homework__homework_id")]
            ),
        )
