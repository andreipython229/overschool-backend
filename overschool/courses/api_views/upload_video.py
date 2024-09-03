from io import BytesIO

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from courses.models.common.base_lesson import BaseLesson, BaseLessonBlock
from courses.serializers import BlockDetailSerializer, BlockUpdateSerializer
from django.core.exceptions import PermissionDenied
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from schools.models import School
from schools.school_mixin import SchoolMixin

from overschool.tasks import upload_video_task

s3 = UploadToS3()


class UploadVideoViewSet(
    WithHeadersViewSet,
    SchoolMixin,
    viewsets.ModelViewSet,
):
    serializer_class = BlockUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["patch"]

    def get_permissions(self, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return permissions
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return (
                BaseLessonBlock.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        user = self.request.user
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return BaseLessonBlock.objects.filter(
                base_lesson__section__course__school__name=school_name
            )

        return BaseLessonBlock.objects.none()

    def update(self, request, *args, **kwargs):

        file_use = self.request.data.get("file_use")
        instance = self.get_object()
        serializer = BlockUpdateSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        video = request.FILES.get("video")
        picture = request.FILES.get("picture")
        if video:
            if instance.video:
                s3.delete_file(str(instance.video))
            base_lesson = BaseLesson.objects.get(pk=instance.base_lesson.id)
            # Отправляем задачу в Huey
            file_path = s3.file_path(video, base_lesson)
            video_stream = BytesIO(video.read())
            upload_video_task(video_stream, file_path)
            serializer.validated_data["video"] = file_path
        if picture:
            if instance.picture:
                s3.delete_file(str(instance.picture))
            base_lesson = BaseLesson.objects.get(pk=instance.base_lesson.id)
            file_path = s3.file_path(picture, base_lesson)
            serializer.validated_data["picture"] = s3.upload_large_file(
                picture, file_path
            )
        elif not video and file_use:
            if instance.video:
                s3.delete_file(str(instance.video))
            instance.video = None
        elif not picture and file_use:
            if instance.picture:
                s3.delete_file(str(instance.picture))
            instance.video = None
        elif not video and not file_use:
            serializer.validated_data["video"] = instance.video
        elif not picture and not file_use:
            serializer.validated_data["picture"] = instance.picture
        instance.save()
        self.perform_update(serializer)

        serializer = BlockDetailSerializer(instance)

        return Response(serializer.data, status=status.HTTP_200_OK)
