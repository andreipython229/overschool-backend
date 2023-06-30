from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models.homework.user_homework import (
    UserHomework,
    UserHomeworkStatusChoices,
)
from courses.models.homework.user_homework_check import UserHomeworkCheck
from courses.paginators import UserHomeworkPagination
from courses.serializers import (
    UserHomeworkCheckDetailSerializer,
    UserHomeworkCheckSerializer,
)
from django.core.exceptions import PermissionDenied
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from schools.models import School
from schools.school_mixin import SchoolMixin


class HomeworkCheckViewSet(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet
):
    """Эндпоинт создания историй проверок домашних заданий ученика.\n
    Cоздавать истории может только ученик и учитель, а так же редактировать исключительно свои истории.
    """

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = UserHomeworkPagination
    http_method_names = ["get", "post", "patch", "put", "head"]

    def get_permissions(self, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(
            group__name__in=["Student", "Teacher", "Admin"], school=school_id
        ).exists():
            return permissions
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_serializer_class(self):
        if self.action in ["retrieve", "update"]:
            return UserHomeworkCheckDetailSerializer
        else:
            return UserHomeworkCheckSerializer

    def get_queryset(self, *args, **kwargs):
        if getattr(self, "swagger_fake_view", False):
            return (
                UserHomework.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
        user = self.request.user

        if user.groups.filter(group__name="Student", school=school_id).exists():
            return UserHomeworkCheck.objects.filter(
                user_homework__user=user,
                user_homework__homework__section__course__school__name=school_name,
            ).order_by("-created_at")
        if user.groups.filter(group__name="Teacher", school=school_id).exists():
            return UserHomeworkCheck.objects.filter(
                user_homework__teacher=user,
                user_homework__homework__section__course__school__name=school_name,
            ).order_by("-created_at")
        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return UserHomeworkCheck.objects.filter(
                user_homework__homework__section__course__school__name=school_name
            ).order_by("-created_at")
        return UserHomeworkCheck.objects.none()

    def create(self, request, *args, **kwargs):
        user = request.user
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
        user_homework = self.request.data.get("user_homework")
        if user_homework is not None:
            user_homeworks = UserHomework.objects.filter(
                homework__section__course__school__name=school_name
            )
            try:
                user_homeworks.get(pk=user_homework)
            except user_homeworks.model.DoesNotExist:
                raise NotFound(
                    "Указанная домашняя работа не относится не к одному курсу этой школы."
                )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_homework_obj = UserHomework.objects.get(pk=user_homework)

        if user.groups.filter(group__name="Student", school=school_id).exists():
            # Логика для студента
            # Проверка, что студент является автором user_homework.user
            if user_homework_obj.user != user:
                return Response(
                    {
                        "status": "Error",
                        "message": "Студент не является автором данного домашнего задания",
                    },
                )
            # Проверка, что статус user_homework не равен "Принято"
            if user_homework_obj.status == UserHomeworkStatusChoices.SUCCESS:
                return Response(
                    {
                        "status": "Error",
                        "message": "Домашнее задание уже принято и нельзя создавать новые проверки",
                    },
                )

            serializer.save(
                status=UserHomeworkStatusChoices.CHECKED,
                author=user,
            )

        elif user.groups.filter(group__name="Teacher", school=school_id).exists():
            # Логика для учителя
            # Проверка, что учитель является преподавателем user_homework.teacher
            if user_homework_obj.teacher != user:
                return Response(
                    {
                        "status": "Error",
                        "message": "Учитель не является преподавателем данного домашнего задания",
                    },
                )
            # Проверка, что статус user_homework не равен "Принято"
            if user_homework_obj.status == UserHomeworkStatusChoices.SUCCESS:
                return Response(
                    {
                        "status": "Error",
                        "message": "Домашнее задание уже принято и нельзя создавать новые проверки",
                    },
                )

            serializer.save(author=user)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs):
        user_homework_check = self.get_object()
        user = request.user

        if user_homework_check.author != user:
            return Response(
                {
                    "status": "Error",
                    "message": "Пользователь может обновлять только свою историю",
                },
            )
        if request.data.get("text"):
            user_homework_check.text = request.data.get("text")
        if (
            request.data.get("status")
            and user_homework_check.user_homework.teacher == user
        ):
            user_homework_check.status = request.data.get("status")
        if (
            request.data.get("mark")
            and user_homework_check.user_homework.teacher == user
        ):
            user_homework_check.mark = request.data.get("mark")

        user_homework_check.save()
        serializer = UserHomeworkCheckDetailSerializer(user_homework_check)

        return Response(serializer.data, status=status.HTTP_200_OK)
