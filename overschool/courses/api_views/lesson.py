from common_services.apply_swagger_auto_schema import apply_swagger_auto_schema
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import SelectelClient
from courses.models import BaseLesson, Course, Lesson, Section, StudentsGroup
from courses.serializers import LessonDetailSerializer, LessonSerializer
from courses.services import LessonProgressMixin
from django.core.exceptions import PermissionDenied
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from schools.models import School
from schools.school_mixin import SchoolMixin

s = SelectelClient()


class LessonViewSet(
    LoggingMixin,
    WithHeadersViewSet,
    LessonProgressMixin,
    SchoolMixin,
    viewsets.ModelViewSet,
):
    """Эндпоинт на получение, создания, изменения и удаления уроков\n
    <h2>/api/{school_name}/lessons/</h2>\n
    Разрешения для просмотра уроков (любой пользователь) \n Разрешения для создания и изменения уроков (только пользователи с группой 'Admin')"""

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
        if self.action in ["list", "retrieve"]:
            # Разрешения для просмотра уроков (любой пользователь школы)
            if user.groups.filter(
                group__name__in=["Student", "Teacher"], school=school_id
            ).exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return LessonDetailSerializer
        else:
            return LessonSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Lesson.objects.none()  # Возвращаем пустой queryset при генерации схемы
        user = self.request.user
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return Lesson.objects.filter(section__course__school__name=school_name)

        if user.groups.filter(group__name="Student", school=school_id).exists():
            course_ids = StudentsGroup.objects.filter(
                course_id__school__name=school_name, students=user
            ).values_list("course_id", flat=True)
            return Lesson.objects.filter(
                active=True, section__course_id__in=course_ids
            )

        if user.groups.filter(group__name="Teacher", school=school_id).exists():
            course_ids = StudentsGroup.objects.filter(
                course_id_id__school__name=school_name, teacher_id=user.pk
            ).values_list("course_id", flat=True)
            return Lesson.objects.filter(
                active=True, section__course_id__in=course_ids
            )

        return Lesson.objects.none()

    def create(self, request, *args, **kwargs):
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

        serializer = LessonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lesson = serializer.save(video=None)

        if request.FILES.get("video"):
            base_lesson = BaseLesson.objects.get(lessons=lesson)
            video = s.upload_file(request.FILES["video"], base_lesson)
            lesson.video = video
            lesson.save()
            serializer = LessonDetailSerializer(lesson)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

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

        instance = self.get_object()
        serializer = LessonSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.FILES.get("video"):
            if instance.video:
                s.remove_from_selectel(str(instance.video))
                segments_to_delete = s.get_folder_files(
                    str(instance.video)[1:], "_segments"
                )
                if segments_to_delete:
                    s.bulk_remove_from_selectel(segments_to_delete, "_segments")
            base_lesson = BaseLesson.objects.get(lessons=instance)
            serializer.validated_data["video"] = s.upload_file(
                request.FILES["video"], base_lesson
            )
        else:
            serializer.validated_data["video"] = instance.video

        self.perform_update(serializer)

        serializer = LessonDetailSerializer(instance)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        files_to_delete = list(
            map(
                lambda el: str(el["file"]),
                list(instance.text_files.values("file"))
                + list(instance.audio_files.values("file")),
            )
        )

        segments_to_delete = []
        if instance.video:
            files_to_delete += str(instance.video)
            segments_to_delete = s.get_folder_files(
                str(instance.video)[1:], "_segments"
            )

        # Удаляем сразу все файлы урока и сегменты видео
        remove_resp = None
        if files_to_delete:
            if s.bulk_remove_from_selectel(files_to_delete) == "Error":
                remove_resp = "Error"
        if segments_to_delete:
            if s.bulk_remove_from_selectel(segments_to_delete, "_segments") == "Error":
                remove_resp = "Error"

        self.perform_destroy(instance)

        if remove_resp == "Error":
            return Response(
                {"error": "Ошибка удаления ресурса из хранилища Selectel"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)


LessonViewSet = apply_swagger_auto_schema(
    tags=[
        "lessons",
    ]
)(LessonViewSet)
