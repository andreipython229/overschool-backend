from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.yandex_client import remove_from_yandex, upload_file
from courses.models import BaseLesson, Lesson
from courses.serializers import LessonDetailSerializer, LessonSerializer
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.response import Response


class LessonViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    """Эндпоинт на получение, создания, изменения и удаления уроков\n
    Разрешения для просмотра уроков (любой пользователь)\n
    Разрешения для создания и изменения уроков (только пользователи с группой 'Admin')"""

    queryset = Lesson.objects.all()
    # serializer_class = LessonSerializer
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action in ["list", "retrieve"]:
            # Разрешения для просмотра уроков (любой пользователь)
            return permissions
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            # Разрешения для создания и изменения уроков (только пользователи с группой 'Admin')
            user = self.request.user
            if user.groups.filter(name="Admin").exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            return permissions

    def get_serializer_class(self):
        if self.action == "retrieve":
            return LessonDetailSerializer
        else:
            return LessonSerializer

    def create(self, request, *args, **kwargs):
        serializer = LessonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lesson = serializer.save(video=None)

        if request.FILES.get("video"):
            base_lesson = BaseLesson.objects.get(lessons=lesson)
            video = upload_file(
                request.FILES["video"], base_lesson, timeout=(2000.0, 10000.0)
            )
            lesson.video = video
            lesson.save()
            serializer = LessonDetailSerializer(lesson)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = LessonSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.FILES.get("video"):
            if instance.video:
                remove_from_yandex(str(instance.video))
            base_lesson = BaseLesson.objects.get(lessons=instance)
            serializer.validated_data["video"] = upload_file(
                request.FILES["video"], base_lesson, timeout=(2000.0, 10000.0)
            )
        else:
            serializer.validated_data["video"] = instance.video

        self.perform_update(serializer)

        serializer = LessonDetailSerializer(instance)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        base_lesson = BaseLesson.objects.get(lessons=instance)
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
