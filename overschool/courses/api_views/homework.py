from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.yandex_client import remove_from_yandex, upload_file
from courses.models import BaseLesson, Homework
from courses.serializers import HomeworkDetailSerializer, HomeworkSerializer
from courses.services import LessonProgressMixin
from django.core.exceptions import PermissionDenied
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response


class HomeworkViewSet(
    LoggingMixin, WithHeadersViewSet, LessonProgressMixin, viewsets.ModelViewSet
):
    """Эндпоинт на получение, создания, изменения и удаления домашних заданий.\n
    Разрешения для просмотра домашних заданий (любой пользователь).\n
    Разрешения для создания и изменения домашних заданий (только пользователи с группой 'Admin')."""

    queryset = Homework.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action in ["list", "retrieve"]:
            # Разрешения для просмотра домашних заданий (любой пользователь)
            return permissions
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            # Разрешения для создания и изменения домашних заданий (только пользователи с группой 'Admin')
            user = self.request.user
            if user.groups.filter(group__name="Admin").exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            return permissions

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_serializer_class(self):
        if self.action == "retrieve":
            return HomeworkDetailSerializer
        else:
            return HomeworkSerializer

    def create(self, request, *args, **kwargs):
        serializer = HomeworkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        homework = serializer.save(video=None)

        if request.FILES.get("video"):
            base_lesson = BaseLesson.objects.get(homeworks=homework)
            video = upload_file(
                request.FILES["video"], base_lesson, timeout=(2000.0, 10000.0)
            )
            homework.video = video
            homework.save()
            serializer = HomeworkDetailSerializer(homework)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = HomeworkSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.FILES.get("video"):
            if instance.video:
                remove_from_yandex(str(instance.video))
            base_lesson = BaseLesson.objects.get(homeworks=instance)
            serializer.validated_data["video"] = upload_file(
                request.FILES["video"], base_lesson, timeout=(2000.0, 10000.0)
            )
        else:
            serializer.validated_data["video"] = instance.video

        self.perform_update(serializer)

        serializer = HomeworkDetailSerializer(instance)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        base_lesson = BaseLesson.objects.get(homeworks=instance)
        course = base_lesson.section.course
        school_id = course.school.school_id

        remove_resp = remove_from_yandex(
            "/{}_school/{}_course/{}_lesson".format(
                school_id, course.course_id, base_lesson.id
            )
        )
        self.perform_destroy(instance)

        if remove_resp == "Error":
            return Response(
                {"error": "Запрашиваемый путь на диске не существует"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)
