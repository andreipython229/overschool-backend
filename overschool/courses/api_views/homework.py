from common_services.apply_swagger_auto_schema import apply_swagger_auto_schema
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import SelectelClient
from courses.models import BaseLesson, Homework, UserHomeworkCheck
from courses.models.courses.section import Section
from courses.serializers import HomeworkDetailSerializer, HomeworkSerializer
from courses.services import LessonProgressMixin
from django.core.exceptions import PermissionDenied
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from schools.models import School
from schools.school_mixin import SchoolMixin

s = SelectelClient()


class HomeworkViewSet(
    LoggingMixin,
    WithHeadersViewSet,
    LessonProgressMixin,
    SchoolMixin,
    viewsets.ModelViewSet,
):
    """Эндпоинт на получение, создания, изменения и удаления домашних заданий.\n
    <h2>/api/{school_name}/homeworks/</h2>
    Разрешения для просмотра домашних заданий (любой пользователь).\n
    Разрешения для создания и изменения домашних заданий (только пользователи с группой 'Admin')."""

    permission_classes = [permissions.IsAuthenticated]
    # parser_classes = (MultiPartParser,)

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
            # Разрешения для просмотра домашних заданий (любой пользователь школы)
            if user.groups.filter(
                group__name__in=["Student", "Teacher"], school=school_id
            ).exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_serializer_class(self):
        if self.action == "retrieve":
            return HomeworkDetailSerializer
        else:
            return HomeworkSerializer

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
        serializer = self.get_serializer(data=request.data)
        serializer.context["request"] = request
        serializer.is_valid(raise_exception=True)
        homework = serializer.save(video=None)

        if request.FILES.get("video"):
            base_lesson = BaseLesson.objects.get(homeworks=homework)
            video = s.upload_file(request.FILES["video"], base_lesson)
            homework.video = video
            homework.save()
            serializer = HomeworkDetailSerializer(
                homework, context={"request": request}
            )

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
        serializer = self.get_serializer(instance, data=request.data)
        serializer.context["request"] = request
        serializer.is_valid(raise_exception=True)

        if request.FILES.get("video"):
            if instance.video:
                s.remove_from_selectel(str(instance.video))
                segments_to_delete = s.get_folder_files(
                    str(instance.video)[1:], "_segments"
                )
                if segments_to_delete:
                    s.bulk_remove_from_selectel(segments_to_delete, "_segments")
            base_lesson = BaseLesson.objects.get(homeworks=instance)
            serializer.validated_data["video"] = s.upload_file(
                request.FILES["video"], base_lesson
            )
        else:
            serializer.validated_data["video"] = instance.video

        self.perform_update(serializer)

        serializer = HomeworkDetailSerializer(instance, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Файлы текста и аудио, связанные с homework
        homework_files = list(instance.text_files.values("file")) + list(
            instance.audio_files.values("file")
        )
        # Файлы текста и аудио, связанные с user_homework
        user_homework_files = []
        user_homeworks = instance.user_homeworks.all()
        for user_homework in user_homeworks:
            user_homework_files += list(user_homework.text_files.values("file")) + list(
                user_homework.audio_files.values("file")
            )
        # Файлы текста и аудио, связанные с user_homework_check
        user_homework_checks_files = []
        user_homework_checks = UserHomeworkCheck.objects.filter(
            user_homework__homework=instance
        )
        for user_homework_check in user_homework_checks:
            user_homework_checks_files += list(
                user_homework_check.text_files.values("file")
            ) + list(user_homework_check.audio_files.values("file"))

        files_to_delete = list(
            map(
                lambda el: str(el["file"]),
                homework_files + user_homework_files + user_homework_checks_files,
            )
        )

        segments_to_delete = []
        if instance.video:
            files_to_delete += str(instance.video)
            segments_to_delete = s.get_folder_files(
                str(instance.video)[1:], "_segments"
            )

        # Удаляем сразу все файлы, связанные с домашней работой, и сегменты видео
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


HomeworkViewSet = apply_swagger_auto_schema(
    tags=[
        "homeworks",
    ]
)(HomeworkViewSet)
