from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.yandex_client import remove_from_yandex
from courses.models import Lesson
from courses.serializers import LessonDetailSerializer, LessonSerializer
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.response import Response


class LessonViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
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

    def destroy(self, request, *args, **kwargs):
        lesson = self.get_object()
        remove_resp = None

        for file_obj in list(lesson.text_files.values("file")) + list(
            lesson.audio_files.values("file")
        ):
            if remove_from_yandex(str(file_obj["file"])) == "Error":
                remove_resp = "Error"

        self.perform_destroy(lesson)

        if remove_resp == "Error":
            return Response(
                {"error": "Запрашиваемый путь на диске не существует"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)
