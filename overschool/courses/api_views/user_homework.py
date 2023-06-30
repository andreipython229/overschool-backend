from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import bulk_remove_from_selectel
from courses.models import BaseLesson, UserHomework, UserHomeworkCheck
from courses.paginators import UserHomeworkPagination
from courses.serializers import (
    UserHomeworkDetailSerializer,
    UserHomeworkSerializer,
    UserHomeworkStatisticsSerializer,
)
from django.contrib.auth.models import AnonymousUser
from django.db.models import OuterRef, Subquery
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from schools.school_mixin import SchoolMixin
from users.models import User


class UserHomeworkViewSet(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet
):
    """Эндпоинт домашних заданий ученика.\n
    Cоздавать дз может только ученик, а так же редактировать и удалять исключительно свои дз
    (свои поля-"text", "file"), учитель подкидывается исходя из группы пользователя.
    """

    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "delete", "head"]

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return UserHomework.objects.none()
        if user.groups.filter(group__name="Student").exists():
            return UserHomework.objects.filter(user=user).order_by("-created_at")
        if user.groups.filter(group__name="Teacher").exists():
            return UserHomework.objects.filter(teacher=user).order_by("-created_at")
        if user.groups.filter(group__name="Admin").exists():
            return UserHomework.objects.all().order_by("-created_at")
        return UserHomework.objects.none()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return UserHomeworkDetailSerializer
        else:
            return UserHomeworkSerializer

    def create(self, request, *args, **kwargs):
        user = request.user
        if isinstance(user, AnonymousUser):
            return Response(
                {"status": "Error", "message": "Пользователь не авторизован"},
            )
        if not user.groups.filter(group__name="Student").exists():
            return Response(
                {"status": "Error", "message": "Недостаточно прав доступа"},
            )
        existing_user_homework = UserHomework.objects.filter(
            user=user, homework=request.data.get("homework")
        ).first()
        if existing_user_homework:
            return Response(
                {"status": "Error", "message": "Объект UserHomework уже существует"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        baselesson = BaseLesson.objects.get(homeworks=request.data.get("homework"))
        teacher_group = user.students_group_fk.filter(
            course_id=baselesson.section.course
        ).first()
        teacher = User.objects.get(id=teacher_group.teacher_id_id)
        if teacher_group.group_settings.task_submission_lock:
            return Response(
                {
                    "status": "Error",
                    "message": "Отправлять домашки запрещено в настройках группы студентов",
                },
            )

        serializer = UserHomeworkSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=user, teacher=teacher)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(
            {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )

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
            # Файлы текста и аудио, связанные с user_homework
            user_homework_files = list(user_homework.text_files.values("file")) + list(
                user_homework.audio_files.values("file")
            )
            # Файлы текста и аудио, связанные с user_homework_check
            user_homework_checks_files = []
            user_homework_checks = user_homework.user_homework_checks.all()
            for user_homework_check in user_homework_checks:
                user_homework_checks_files += list(
                    user_homework_check.text_files.values("file")
                ) + list(user_homework_check.audio_files.values("file"))

            files_to_delete = list(
                map(
                    lambda el: str(el["file"]),
                    user_homework_files + user_homework_checks_files,
                )
            )
            # Удаляем сразу все файлы, связанные с домашней работой пользователя и ее доработками
            remove_resp = bulk_remove_from_selectel(files_to_delete)

            self.perform_destroy(user_homework)

            if remove_resp == "Error":
                return Response(
                    {"error": "Ошибка удаления ресурса из хранилища Selectel"},
                    status=status.HTTP_204_NO_CONTENT,
                )
            else:
                return Response(status=status.HTTP_204_NO_CONTENT)


class HomeworkStatisticsView(LoggingMixin, WithHeadersViewSet, generics.ListAPIView):
    """Эндпоинт возвращает стаитстику по домашним работам\n
    Эндпоинт возвращает стаитстику по домашним работам"""

    serializer_class = UserHomeworkStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = UserHomeworkPagination

    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        queryset = UserHomework.objects.none()
        if user.is_anonymous:
            return queryset
        if user.groups.filter(group__name="Student").exists():
            queryset = UserHomework.objects.filter(user=user).order_by("-created_at")
        if user.groups.filter(group__name="Teacher").exists():
            queryset = UserHomework.objects.filter(teacher=user).order_by("-created_at")
        if user.groups.filter(group__name="Admin").exists():
            queryset = UserHomework.objects.all().order_by("-created_at")

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
                homework__name__icontains=self.request.GET.get("homework_name")
            )

        if self.request.GET.get("group_name"):
            queryset = queryset.filter(
                user__students_group_fk__name=self.request.GET.get("group_name")
            )

        if self.request.GET.get("start_date"):
            subquery = UserHomeworkCheck.objects.filter(
                user_homework=OuterRef("pk")
            ).order_by("-updated_at")[:1]
            queryset = queryset.annotate(
                last_check_updated_at=Subquery(subquery.values("updated_at"))
            )
            queryset = queryset.filter(
                last_check_updated_at__gte=self.request.GET.get("start_date")
            )

        if self.request.GET.get("end_date"):
            subquery = UserHomeworkCheck.objects.filter(
                user_homework=OuterRef("pk")
            ).order_by("-updated_at")[:1]
            queryset = queryset.annotate(
                last_check_updated_at=Subquery(subquery.values("updated_at"))
            )
            queryset = queryset.filter(
                last_check_updated_at__lte=self.request.GET.get("end_date")
            )
        return queryset
