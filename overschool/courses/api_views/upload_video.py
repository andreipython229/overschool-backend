from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from courses.models import BaseLesson, Homework, Lesson, Section, StudentsGroup
from courses.serializers import (
    HomeworkDetailSerializer,
    HomeworkSerializer,
    LessonDetailSerializer,
    LessonSerializer,
)
from courses.services import LessonProgressMixin
from django.core.exceptions import PermissionDenied
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from schools.models import School
from schools.school_mixin import SchoolMixin

s3 = UploadToS3()


class HomeworkVideoViewSet(
    LoggingMixin,
    WithHeadersViewSet,
    LessonProgressMixin,
    SchoolMixin,
    viewsets.ModelViewSet,
):
    serializer_class = HomeworkSerializer
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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_queryset(self, *args, **kwargs):
        if getattr(self, "swagger_fake_view", False):
            return (
                Homework.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
        user = self.request.user

        if user.groups.filter(group__name="Student", school=school_id).exists():
            students_group = user.students_group_fk.all().values_list(
                "course_id", flat=True
            )
            return Homework.objects.filter(
                section__course__school__name=school_name,
                section__course__in=students_group,
            )
        if user.groups.filter(group__name="Teacher", school=school_id).exists():
            teacher_group = user.teacher_group_fk.all().values_list(
                "course_id", flat=True
            )
            return Homework.objects.filter(
                section__course__school__name=school_name,
                section__course__in=teacher_group,
            )
        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return Homework.objects.filter(section__course__school__name=school_name)
        return Homework.objects.none()

    def update(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        section = self.request.data.get("section")
        if section is not None:
            sections = Section.objects.filter(course__school__name=school_name)
            try:
                sections.get(pk=section)
            except sections.model.DoesNotExist:
                raise NotFound(
                    "Указанная секция не относится не к одному курсу этой школы."
                )
        video_use = self.request.data.get("video_use")
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.context["request"] = request
        serializer.is_valid(raise_exception=True)

        video = request.FILES.get("video")
        if video:
            if instance.video:
                s3.delete_file(str(instance.video))
            base_lesson = BaseLesson.objects.get(homeworks=instance)
            serializer.validated_data["video"] = s3.upload_large_file(
                request.FILES["video"], base_lesson
            )
        elif not video and video_use:
            if instance.video:
                s3.delete_file(str(instance.video))
            instance.video = None
        elif not video and not video_use:
            serializer.validated_data["video"] = instance.video
        instance.save()
        self.perform_update(serializer)

        serializer = HomeworkDetailSerializer(instance, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)


class LessonVideoViewSet(
    LoggingMixin,
    WithHeadersViewSet,
    LessonProgressMixin,
    SchoolMixin,
    viewsets.ModelViewSet,
):
    serializer_class = LessonSerializer
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
                Lesson.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        user = self.request.user
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return Lesson.objects.filter(section__course__school__name=school_name)

        if user.groups.filter(group__name="Student", school=school_id).exists():
            course_ids = StudentsGroup.objects.filter(
                course_id__school__name=school_name, students=user
            ).values_list("course_id", flat=True)
            return Lesson.objects.filter(active=True, section__course_id__in=course_ids)

        if user.groups.filter(group__name="Teacher", school=school_id).exists():
            course_ids = StudentsGroup.objects.filter(
                course_id_id__school__name=school_name, teacher_id=user.pk
            ).values_list("course_id", flat=True)
            return Lesson.objects.filter(active=True, section__course_id__in=course_ids)

        return Lesson.objects.none()

    def update(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")

        section = self.request.data.get("section")

        if section is not None:
            sections = Section.objects.filter(course__school__name=school_name)
            try:
                sections.get(pk=section)
            except sections.model.DoesNotExist:
                raise NotFound(
                    "Указанная секция не относится не к одному курсу этой школы."
                )
        video_use = self.request.data.get("video_use")
        instance = self.get_object()
        serializer = LessonSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        if not request.data.get("active"):
            serializer.validated_data["active"] = instance.active

        video = request.FILES.get("video")
        if video:
            if instance.video:
                s3.delete_file(str(instance.video))
            base_lesson = BaseLesson.objects.get(lessons=instance)
            serializer.validated_data["video"] = s3.upload_large_file(
                request.FILES["video"], base_lesson
            )
        elif not video and video_use:
            if instance.video:
                s3.delete_file(str(instance.video))
            instance.video = None
        elif not video and not video_use:
            serializer.validated_data["video"] = instance.video
        instance.save()
        self.perform_update(serializer)

        serializer = LessonDetailSerializer(instance)

        return Response(serializer.data, status=status.HTTP_200_OK)
