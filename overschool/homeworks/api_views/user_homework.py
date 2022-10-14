from django_filters.rest_framework import DjangoFilterBackend
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.db.models import F, Max, Q
from django.db.models.expressions import Window
from homeworks.models import UserHomework
from users.models import User
from homeworks.paginators import UserHomeworkPagination
from homeworks.serializers import (
    UserHomeworkSerializer,
    UserHomeworkStatisticsSerializer,
    TeacherHomeworkSerializer,
    AllUserHomeworkSerializer,
)
from django.contrib.auth.models import AnonymousUser
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response


class AllUserHomeworkViewSet(WithHeadersViewSet, viewsets.ModelViewSet, generics.ListAPIView):
    """
    Эндпоинт на получение всё домашних работ учеников с фильтрами по полям ("user", "teacher")
    """
    queryset = UserHomework.objects.all()
    serializer_class = AllUserHomeworkSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["user", "teacher"]
    http_method_names = ["get", "head"]
    permission_classes = [permissions.DjangoModelPermissions]


class UserHomeworkViewSet(WithHeadersViewSet, viewsets.ModelViewSet):
    """
    Cоздавать дз может только ученик, а так же редактировать и удалять исключительно свои дз
    (свои поля-"text", "file"), учитель подкидывается исходя из группы пользователя.
    """
    queryset = UserHomework.objects.all()
    serializer_class = UserHomeworkSerializer
    permission_classes = [permissions.DjangoModelPermissions]

    def create(self, request, *args, **kwargs):
        user = self.request.user
        if isinstance(user, AnonymousUser):
            return Response(
                {"status": "Error", "message": "Пользователь не авторизирован"},
            )
        teacher_group = user.students_group_fk.get()
        teacher = User.objects.get(id=teacher_group.teacher_id_id)

        serializer = UserHomeworkSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=user, teacher=teacher)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            {"error": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

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

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = self.request.user
        homeworks = UserHomework.objects.get(pk=instance.pk)
        if homeworks.user != user:
            return Response(
                {"status": "Error", "message": "Пользователь может удалить только свою домашнюю работу"},
            )
        else:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)


class TeacherHomeworkViewSet(WithHeadersViewSet, viewsets.ModelViewSet):
    """
    Учитель может редактировать и удалять только дз своих учеников
    и свои поля ("status", "mark", "teacher_message“).
    """
    queryset = UserHomework.objects.all()
    serializer_class = TeacherHomeworkSerializer
    permission_classes = [permissions.DjangoModelPermissions]
    http_method_names = ["get", "patch", "put", "head", "delete"]

    def update(self, request, *args, **kwargs):
        user_homework = self.get_object()
        user = self.request.user
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

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = self.request.user
        homeworks = UserHomework.objects.get(pk=instance.pk)
        if homeworks.teacher != user:
            return Response(
                {"status": "Error", "message": "Учитель может удалять домашние работы только своей группы"},
            )
        else:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)


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
