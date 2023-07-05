from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.models import AudioFile
from common_services.selectel_client import remove_from_selectel, upload_file
from common_services.serializers import AudioFileSerializer
from courses.models import BaseLesson, UserHomework
from courses.models.homework.user_homework import UserHomework
from courses.models.homework.user_homework_check import UserHomeworkCheck
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from schools.school_mixin import SchoolMixin

from schools.models import School

from common_services.services.request_params import FileParams


class AudioFileViewSet(LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet):
    """
    Модель добавления аудиофайлов к урокам и занятиям\n
    <h2>/api/{school_name}/audio_files/</h2>\n
    Модель добавления аудиофайлов к урокам и занятиям
    """

    serializer_class = AudioFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["post", "delete", "head"]
    parser_classes = (MultiPartParser,)

    def get_permissions(self, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name__in=["Student", "Teacher", "Admin"], school=school_id).exists():
            return permissions
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_queryset(self, *args, **kwargs):
        if getattr(self, "swagger_fake_view", False):
            return (
                AudioFile.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        school_name = self.kwargs.get("school_name")
        return AudioFile.objects.filter(
            Q(base_lesson__section__course__school__name=school_name) |
            Q(user_homework__homework__section__course__school__name=school_name) |
            Q(user_homework_check__user_homework__homework__section__course__school__name=school_name)
        )

    @swagger_auto_schema(
        tags=["files"],
        manual_parameters=[
            FileParams.base_lesson,
            FileParams.user_homework,
            FileParams.user_homework_check,
            FileParams.files
        ],
        operation_description="Пользователь с ролью Admin указывает base_lesson соотвествующего объекта, пользователи "
                              "с ролью Student или Teacher указывают user_homework или user_homework_check "
                              "соотвествующего объектa",
        operation_summary="Эндпоинт работы с файлами",
    )
    def create(self, request, *args, **kwargs):
        user = request.user
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        # Проверяем, что пользователь студент или учитель
        if user.groups.filter(group__name__in=["Student", "Teacher"], school=school_id).exists():
            user_homework_id = request.data.get("user_homework")
            user_homework_check_id = request.data.get("user_homework_check")

            if user_homework_id:
                # Проверяем, что пользователь является автором указанной домашней работы
                user_homework = UserHomework.objects.filter(
                    user_homework_id=user_homework_id, user=user
                ).first()

                if user_homework:
                    user_homeworks = UserHomework.objects.filter(
                        homework__section__course__school__name=school_name)
                    try:
                        user_homeworks.get(pk=user_homework_id)
                    except user_homeworks.model.DoesNotExist:
                        raise NotFound(
                            "Указанный user_homework не относится не к одному занятию этой школы."
                        )
                    files_list = request.data.getlist("files")
                    created_files = []
                    if files_list:
                        for uploaded_file in files_list:
                            base_lesson = BaseLesson.objects.get(
                                homeworks=user_homework.homework
                            )
                            serializer = self.get_serializer(data=request.data)
                            serializer.is_valid(raise_exception=True)
                            # Загружаем файл в Selectel и получаем путь к файлу в хранилище
                            file_path = upload_file(uploaded_file, base_lesson)
                            serializer.save(author=user, file=file_path)
                            created_files.append(serializer.data)
                        return Response(created_files, status=status.HTTP_201_CREATED)
                else:
                    return Response(
                        {
                            "error": "Пользователь не является автором указанной домашней работы"
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )
            if user_homework_check_id:
                user_homework_check = UserHomeworkCheck.objects.filter(
                    user_homework_check_id=user_homework_check_id, author=user
                ).first()

                if user_homework_check:
                    user_homework_checks = UserHomeworkCheck.objects.filter(
                        user_homework__homework__section__course__school__name=school_name)
                    try:
                        user_homework_checks.get(pk=user_homework_check_id)
                    except user_homework_checks.model.DoesNotExist:
                        raise NotFound(
                            "Указанный user_homework_checks не относится не к одному занятию этой школы."
                        )
                    files_list = request.data.getlist("files")
                    created_files = []
                    if files_list:
                        for uploaded_file in files_list:
                            base_lesson = BaseLesson.objects.get(
                                homeworks=user_homework_check.user_homework.homework
                            )
                            serializer = self.get_serializer(data=request.data)
                            serializer.is_valid(raise_exception=True)
                            # Загружаем файл в Selectel и получаем путь к файлу в хранилище
                            file_path = upload_file(uploaded_file, base_lesson)
                            serializer.save(author=user, file=file_path)
                            created_files.append(serializer.data)
                        return Response(created_files, status=status.HTTP_201_CREATED)
                else:
                    return Response(
                        {
                            "error": "Пользователь не является автором указанной проверки домашней работы"
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

            else:
                return Response(
                    {
                        "error": "Не указан идентификатор домашней работы (user_homework) или проверки (user_homework_check)"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Проверяем, что пользователь админ
        elif user.groups.filter(group__name="Admin", school=school_id).exists():
            base_lesson_id = request.data.get("base_lesson")

            if base_lesson_id:
                base_lessons = BaseLesson.objects.filter(section_id__course__school__name=school_name)
                try:
                    base_lessons.get(pk=base_lesson_id)
                except base_lessons.model.DoesNotExist:
                    raise NotFound(
                        "Указанный base_lessons не относится не к одному занятию этой школы."
                    )
                files_list = request.data.getlist("files")
                created_files = []
                if files_list:
                    for uploaded_file in files_list:
                        base_lesson = BaseLesson.objects.get(id=base_lesson_id)
                        serializer = self.get_serializer(data=request.data)
                        serializer.is_valid(raise_exception=True)
                        # Загружаем файл в Selectel и получаем путь к файлу в хранилище
                        file_path = upload_file(uploaded_file, base_lesson)
                        serializer.save(author=user, file=file_path)
                        created_files.append(serializer.data)
                    return Response(created_files, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {"error": "Не указан идентификатор базового урока ('base_lesson')"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {"error": "У вас нет прав для выполнения этого действия"},
                status=status.HTTP_403_FORBIDDEN,
            )

    @swagger_auto_schema(
        tags=["files"],
        operation_description="Удаление файлов по id файлы может удалять автор или Админ школы",
        operation_summary="Эндпоинт работы с файлами",
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        if (
                user != instance.author
                and not user.groups.filter(group__name="Admin", school=school_id).exists()
        ):
            return Response(
                {"error": "Вы не являетесь автором этого файла"},
                status=status.HTTP_403_FORBIDDEN,
            )

        self.perform_destroy(instance)
        if remove_from_selectel(str(instance.file)) == "Success":
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {"error": "Ошибка удаления ресурса из хранилища Selectel"},
                status=status.HTTP_204_NO_CONTENT,
            )
