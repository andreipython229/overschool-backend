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
from django.contrib.auth.models import AnonymousUser
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response


class HomeworkCheckViewSet(WithHeadersViewSet, viewsets.ModelViewSet):
    """Эндпоинт создания историй проверок домашних заданий ученика.\n
    Cоздавать истории может только ученик и учитель, а так же редактировать исключительно свои истории.
    """

    queryset = UserHomeworkCheck.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = UserHomeworkPagination
    http_method_names = ["get", "post", "patch", "put", "head"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return UserHomeworkCheckDetailSerializer
        else:
            return UserHomeworkCheckSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return UserHomeworkCheck.objects.none()
        if user.groups.filter(group__name="Student").exists():
            return UserHomeworkCheck.objects.filter(user_homework__user=user).order_by(
                "-created_at"
            )
        if user.groups.filter(group__name="Teacher").exists():
            return UserHomeworkCheck.objects.filter(
                user_homework__teacher=user
            ).order_by("-created_at")
        if user.groups.filter(group__name="Admin").exists():
            return UserHomeworkCheck.objects.all().order_by("-created_at")
        return UserHomeworkCheck.objects.none()

    def create(self, request, *args, **kwargs):
        user = request.user
        if isinstance(user, AnonymousUser):
            return Response(
                {"status": "Error", "message": "Пользователь не авторизован"},
            )
        if (
            not user.groups.filter(group__name="Student").exists()
            and not user.groups.filter(group__name="Teacher").exists()
        ):
            return Response(
                {"status": "Error", "message": "Недостаточно прав доступа"},
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_homework_id = serializer.validated_data["user_homework"].pk
        user_homework = UserHomework.objects.get(pk=user_homework_id)

        if user.groups.filter(group__name="Student").exists():
            # Логика для студента

            # Проверка, что студент является автором user_homework.user
            if user_homework.user != user:
                return Response(
                    {
                        "status": "Error",
                        "message": "Студент не является автором данного домашнего задания",
                    },
                )

            # Проверка, что статус user_homework не равен "Принято"
            if user_homework.status == UserHomeworkStatusChoices.SUCCESS:
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

        elif user.groups.filter(group__name="Teacher").exists():
            # Логика для учителя

            # Проверка, что учитель является преподавателем user_homework.teacher
            if user_homework.teacher != user:
                return Response(
                    {
                        "status": "Error",
                        "message": "Учитель не является преподавателем данного домашнего задания",
                    },
                )
            # Проверка, что статус user_homework не равен "Принято"
            if user_homework.status == UserHomeworkStatusChoices.SUCCESS:
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
        serializer = UserHomeworkCheckSerializer(user_homework_check)

        return Response(serializer.data, status=status.HTTP_200_OK)
