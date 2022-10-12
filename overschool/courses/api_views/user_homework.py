from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import UserHomework
from courses.paginators import UserHomeworkPagination
from courses.serializers import (
    TeacherHomeworkSerializer,
    UserHomeworkSerializer,
    UserHomeworkStatisticsSerializer,
)
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.db.models import F, Max, Q
from django.db.models.expressions import Window
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response


class UserHomeworkViewSet(WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = UserHomework.objects.all()
    serializer_class = UserHomeworkSerializer
    # permission_classes = [permissions.DjangoModelPermissions]

    def create(self, request, *args, **kwargs):
        user = self.request.user
        if isinstance(user, AnonymousUser):
            return Response(
                {"status": "Error", "message": "Пользователь не авторизирован"},
            )
        teacher_group = user.students_group_fk.get()
        teacher = settings.AUTH_USER_MODEL.objects.get(id=teacher_group.teacher_id_id)

        serializer = UserHomeworkSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=user, teacher=teacher)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        user_homework = self.get_object()
        user = self.request.user

        homeworks = UserHomework.objects.get(pk=user_homework.pk)
        if homeworks.user != user:
            return Response(
                {"status": "Error", "message": "Пользователь может обновлять только свою домашнюю работу"},
            )
        else:
            if request.data.get("text"):
                homeworks.text = request.data.get("text")
            if request.data.get("file"):
                homeworks.file = request.data.get("file")

            serializer = UserHomeworkSerializer(homeworks)

            return Response(serializer.data, status=status.HTTP_200_OK)


class TeacherHomeworkViewSet(WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = UserHomework.objects.all()
    serializer_class = TeacherHomeworkSerializer
    permission_classes = [permissions.DjangoModelPermissions]

    def create(self, request, *args, **kwargs):
        return Response(
            {"status": "Error", "message": "Не доступно для учителя"},
        )

    def update(self, request, *args, **kwargs):
        user_homework = self.get_object()
        user = self.request.user
        print(user)
        homeworks = UserHomework.objects.get(pk=user_homework.pk)
        if homeworks.teacher != user:
            return Response(
                {"status": "Error", "message": "Учитель может обновлять домашние работы только своей группы"},
            )
        else:
            if request.data.get("teacher_message"):
                homeworks.teacher_message = request.data.get("teacher_message")
            if request.data.get("mark"):
                homeworks.mark = request.data.get("mark")
            if request.data.get("status"):
                homeworks.status = request.data.get("status")

            serializer = UserHomeworkSerializer(homeworks)

            return Response(serializer.data, status=status.HTTP_200_OK)


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
