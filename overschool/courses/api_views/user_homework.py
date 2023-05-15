from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import Course, UserHomework
from courses.paginators import UserHomeworkPagination
from courses.serializers import (
    AllUserHomeworkSerializer,
    TeacherHomeworkSerializer,
    UserHomeworkSerializer,
    UserHomeworkStatisticsSerializer,
)
from django.contrib.auth.models import AnonymousUser
from django.db.models import F, Max
from django.db.models.expressions import Window
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from users.models import User


class AllUserHomeworkViewSet(
    WithHeadersViewSet, viewsets.ModelViewSet, generics.ListAPIView
):
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

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return UserHomework.objects.none()
        if user.groups.filter(name="Student").exists():
            return UserHomework.objects.filter(user=user)
        return UserHomework.objects.none()

    def create(self, request, *args, **kwargs):
        user = request.user
        if isinstance(user, AnonymousUser):
            return Response(
                {"status": "Error", "message": "Пользователь не авторизован"},
            )
        if not user.groups.filter(name="Student").exists():
            return Response(
                {"status": "Error", "message": "Недостаточно прав доступа"},
            )
        homework_id = request.data["homework"]
        course_id = (
            Course.objects.filter(sections__all_lessons__homeworks=homework_id)
            .values("course_id")
            .first()["course_id"]
        )
        teacher_group = user.students_group_fk.filter(course_id=course_id).first()
        teacher = User.objects.get(id=teacher_group.teacher_id_id)

        serializer = UserHomeworkSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=user, teacher=teacher)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(
            {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )

    def update(self, request, *args, **kwargs):
        user_homework = self.get_object()
        user = request.user

        if user_homework.user != user:
            return Response(
                {
                    "status": "Error",
                    "message": "Пользователь может обновлять только свою домашнюю работу",
                },
            )
        else:
            if request.data.get("text"):
                user_homework.text = request.data.get("text")

            user_homework.save()
            serializer = UserHomeworkSerializer(user_homework)

            return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        user_homework = self.get_object()
        user = request.user

        if user_homework.user != user:
            return Response(
                {
                    "status": "Error",
                    "message": "Пользователь может удалить только свою домашнюю работу",
                },
            )
        else:
            self.perform_destroy(user_homework)
            return Response(status=status.HTTP_204_NO_CONTENT)


class TeacherHomeworkViewSet(WithHeadersViewSet, viewsets.ModelViewSet):
    """
    Учитель может редактировать и удалять только дз своих учеников
    и свои поля ("status", "mark", "teacher_message“).
    """

    queryset = UserHomework.objects.all()
    serializer_class = TeacherHomeworkSerializer
    permission_classes = [permissions.DjangoModelPermissions]
    http_method_names = ["get", "patch", "put", "head"]

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return UserHomework.objects.none()
        if user.groups.filter(name="Teacher").exists():
            return UserHomework.objects.filter(teacher=user)
        return UserHomework.objects.none()

    def update(self, request, *args, **kwargs):
        user_homework = self.get_object()
        user = request.user
        if user_homework.teacher != user:
            return Response(
                {
                    "status": "Error",
                    "message": "Учитель может обновлять домашние работы только своей группы",
                },
            )
        else:
            if request.data.get("teacher_message"):
                user_homework.teacher_message = request.data.get("teacher_message")
            if request.data.get("mark"):
                user_homework.mark = request.data.get("mark")
            if request.data.get("status"):
                user_homework.status = request.data.get("status")

            user_homework.save()
            serializer = UserHomeworkSerializer(user_homework)

            return Response(serializer.data, status=status.HTTP_200_OK)


class HomeworkStatisticsView(LoggingMixin, WithHeadersViewSet, generics.ListAPIView):
    serializer_class = UserHomeworkStatisticsSerializer
    queryset = UserHomework.objects.all()
    permission_classes = [permissions.DjangoModelPermissions]
    pagination_class = UserHomeworkPagination

    def get_queryset(self, *args, **kwargs):
        queryset = UserHomework.objects.all()

        if self.request.GET.get("status"):
            queryset = queryset.filter(status=self.request.GET.get("status"))

        if self.request.GET.get("start_mark"):
            queryset = queryset.filter(mark__gte=self.request.GET.get("start_mark"))

        if self.request.GET.get("end_mark"):
            queryset = queryset.filter(mark__lte=self.request.GET.get("end_mark"))

        if self.request.GET.get("mark"):
            queryset = queryset.filter(mark=self.request.GET.get("mark"))

        if self.request.GET.get("course_name"):
            queryset = queryset.filter(
                homework__section__course__name=self.request.GET.get("course_name")
            )

        if self.request.GET.get("homework_name"):
            queryset = queryset.filter(
                homework__name=self.request.GET.get("homework_name")
            )

        if self.request.GET.get("group_name"):
            queryset = queryset.filter(
                user__students_group_fk__name=self.request.GET.get("group_name")
            )

        if self.request.GET.get("start_date"):
            queryset = queryset.filter(
                updated_at__gte=self.request.GET.get("start_date")
            )

        if self.request.GET.get("end_date"):
            queryset = queryset.filter(updated_at__lte=self.request.GET.get("end_date"))

        return queryset.values(
            "mark",
            "status",
            "homework",
            avatar=F("user__profile__avatar"),
            user_name=F("user__first_name"),
            user_lastname=F("user__last_name"),
            email=F("user__email"),
            course_name=F("homework__section__course__name"),
            homework_name=F("homework__name"),
            group_id=F("user__groups"),
            group_name=F("user__students_group_fk__name"),
            h_history=F("homework__user_homeworks__status"),
            last_update=Window(
                expression=Max("updated_at"),
                partition_by=[F("user__email"), F("homework__homework_id")],
            ),
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
