from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import BaseLesson, BaseLessonBlock
from courses.serializers import LessonBlockSerializer
from django.core.exceptions import PermissionDenied
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from schools.models import School
from schools.school_mixin import SchoolMixin


class LessonAvailabilityViewSet(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet
):
    queryset = BaseLessonBlock.objects.all()
    serializer_class = LessonBlockSerializer
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
        serializer.save()

        # if request.FILES.get("video"):
        #     base_lesson = BaseLesson.objects.get(lessons=lesson)
        #     video = s3.upload_large_file(request.FILES["video"], base_lesson)
        #     lesson.video = video
        #     lesson.save()
        #     serializer = LessonDetailSerializer(lesson)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
