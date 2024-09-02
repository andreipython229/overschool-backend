from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from courses.models.common.base_lesson import BaseLesson, BaseLessonBlock
from courses.serializers import BlockDetailSerializer, BlockUpdateSerializer
from django.core.exceptions import PermissionDenied
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from schools.models import School
from schools.school_mixin import SchoolMixin

s3 = UploadToS3()

executor = ThreadPoolExecutor()


def upload_video_in_background(video, base_lesson, instance):
    video_url = s3.upload_large_file(video, base_lesson)
    instance.video = video_url
    instance.save()


def upload_picture_in_background(picture, base_lesson, instance):
    picture_url = s3.upload_large_file(picture, base_lesson)
    instance.picture = picture_url
    instance.save()


def delete_video_in_background(instance):
    if instance.video:
        s3.delete_file(str(instance.video))
    instance.video = None
    instance.save()


def delete_picture_in_background(instance):
    if instance.picture:
        s3.delete_file(str(instance.picture))
    instance.picture = None
    instance.save()


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
            # Запускаем удаление старого видео в фоне
            executor.submit(delete_video_in_background, instance)
            # Запускаем загрузку нового видео в фоне
            base_lesson = BaseLesson.objects.get(pk=instance.base_lesson.id)
            executor.submit(upload_video_in_background, video, base_lesson, instance)

        if picture:
            # Запускаем удаление старой картинки в фоне
            executor.submit(delete_picture_in_background, instance)
            # Запускаем загрузку новой картинки в фоне
            base_lesson = BaseLesson.objects.get(pk=instance.base_lesson.id)
            executor.submit(
                upload_picture_in_background, picture, base_lesson, instance
            )

        # Если не было ни видео, ни картинок, то удаляем в фоне
        if not video and file_use:
            executor.submit(delete_video_in_background, instance)

        if not picture and file_use:
            executor.submit(delete_picture_in_background, instance)
        course = base_lesson.section.course
        course_id = course.course_id
        school_id = course.school.school_id
        file_path = "{}_school/{}_course/{}_lesson/{}@{}".format(
            school_id, course_id, base_lesson.id, datetime.now(), video
        ).replace(" ", "_")
        serializer.validated_data["video"] = file_path
        # Сохраняем изменения в объекте
        self.perform_update(serializer)

        # Возвращаем ответ сразу, не дожидаясь завершения фона
        serializer = BlockDetailSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
