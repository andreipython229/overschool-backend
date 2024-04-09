from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from courses.models import BaseLesson, BaseLessonBlock, BlockButton
from courses.serializers import (
    BlockButtonSerializer,
    BlockDetailSerializer,
    BlockUpdateSerializer,
    LessonBlockSerializer,
    LessonOrderSerializer,
)
from django.core.exceptions import PermissionDenied
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from schools.models import School
from schools.school_mixin import SchoolMixin

s3 = UploadToS3()


class BaseLessonBlockViewSet(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet
):
    queryset = BaseLessonBlock.objects.all()
    http_method_names = ["post", "delete", "patch"]
    permission_classes = [permissions.IsAuthenticated]

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

    def get_serializer_class(self):
        if self.action == "perform_update":
            return BlockUpdateSerializer
        else:
            return LessonBlockSerializer

    def create(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        base_lesson = self.request.data.get("base_lesson")
        if base_lesson is not None:
            base_lessons = BaseLesson.objects.filter(
                section__course__school__name=school_name
            )
            try:
                base_lessons.get(pk=base_lesson)
            except base_lesson.model.DoesNotExist:
                raise NotFound(
                    "Указанный базовый урок не относится ни к одному курсу этой школы."
                )

        serializer = LessonBlockSerializer(data={**request.data})
        serializer.is_valid(raise_exception=True)
        block = serializer.save()

        if request.FILES.get("video"):
            base_lesson_obj = BaseLesson.objects.get(pk=base_lesson)
            video = s3.upload_large_file(request.FILES["video"], base_lesson_obj)
            block.video = video
            block.save()
        if request.FILES.get("picture"):
            base_lesson_obj = BaseLesson.objects.get(pk=base_lesson)
            picture = s3.upload_large_file(request.FILES["picture"], base_lesson_obj)
            block.picture = picture
            block.save()

        serializer = LessonBlockSerializer(block)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

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
            serializer.validated_data["video"] = s3.upload_large_file(
                request.FILES["video"], base_lesson
            )
        if picture:
            if instance.picture:
                s3.delete_file(str(instance.picture))
            base_lesson = BaseLesson.objects.get(pk=instance.base_lesson.id)
            serializer.validated_data["picture"] = s3.upload_large_file(
                request.FILES["picture"], base_lesson
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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.video:
            s3.delete_file(str(instance.video))
        if instance.picture:
            s3.delete_file(str(instance.picture))

        self.perform_destroy(instance)

        return Response(status=status.HTTP_204_NO_CONTENT)


class BlockButtonViewSet(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet
):
    http_method_names = ["post", "delete", "patch"]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BlockButtonSerializer

    def get_permissions(self, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin", school=school).exists():
            return permissions
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return (
                BlockButton.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        user = self.request.user
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)

        if user.groups.filter(group__name="Admin", school=school).exists():
            return BlockButton.objects.filter(
                block__base_lesson__section__course__school__name=school_name
            )

        return BlockButton.objects.none()

    def create(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        block = self.request.data.get("block")
        if block is not None:
            blocks = BaseLessonBlock.objects.filter(
                base_lesson__section__course__school__name=school_name, type="buttons"
            )
            try:
                blocks.get(pk=block)
            except block.model.DoesNotExist:
                raise NotFound("В вашей школе не найден такой блок нужного типа.")

        serializer = BlockButtonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        block = self.request.data.get("block")
        if block is not None:
            blocks = BaseLessonBlock.objects.filter(
                base_lesson__section__course__school__name=school_name, type="buttons"
            )
            try:
                blocks.get(pk=block)
            except block.model.DoesNotExist:
                raise NotFound("В вашей школе не найден такой блок нужного типа.")

        instance = self.get_object()
        serializer = BlockButtonSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data, status=status.HTTP_200_OK)


class BlockUpdateViewSet(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, generics.GenericAPIView
):
    serializer_class = None

    @swagger_auto_schema(method="post", request_body=LessonOrderSerializer)
    @action(detail=False, methods=["POST"])
    def shuffle_blocks(self, request, *args, **kwargs):

        data = request.data

        # сериализатор с полученными данными
        serializer = LessonOrderSerializer(data=data, many=True)

        if serializer.is_valid():
            for block_data in serializer.validated_data:
                block_id = block_data["block_id"]
                new_order = block_data["order"]

                # Обновите порядок блока в базе данных
                try:
                    block = BaseLessonBlock.objects.get(id=block_id)
                    block.order = new_order
                    block.save()
                except Exception as e:
                    return Response(str(e), status=500)
            return Response("Блоки успешно обновлены", status=status.HTTP_200_OK)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
