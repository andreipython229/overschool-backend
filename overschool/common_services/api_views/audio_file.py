from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.models import AudioFile
from common_services.selectel_client import SelectelClient
from common_services.serializers import AudioFileSerializer
from courses.models import BaseLesson, UserHomework
from courses.models.homework.user_homework import UserHomework
from courses.models.homework.user_homework_check import UserHomeworkCheck
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response

s = SelectelClient()


class AudioFileViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    """
    Модель добавления аудиофайлов к урокам и занятиям\n
    Модель добавления аудиофайлов к урокам и занятиям
    """

    queryset = AudioFile.objects.all()
    serializer_class = AudioFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["post", "delete", "head"]

    def create(self, request, *args, **kwargs):
        user = request.user

        # Проверяем, что пользователь студент или учитель
        if (
            user.groups.filter(group__name="Student").exists()
            or user.groups.filter(group__name="Teacher").exists()
        ):
            user_homework_id = request.data.get("user_homework")
            user_homework_check_id = request.data.get("user_homework_check")

            if user_homework_id:
                # Проверяем, что пользователь является автором указанной домашней работы
                user_homework = UserHomework.objects.filter(
                    user_homework_id=user_homework_id, user=user
                ).first()

                if user_homework:
                    serializer = self.get_serializer(data=request.data)
                    serializer.is_valid(raise_exception=True)

                    uploaded_file = request.FILES["file"]
                    base_lesson = BaseLesson.objects.get(
                        homeworks=user_homework.homework
                    )
                    # Загружаем файл в Selectel и получаем путь к файлу в хранилище
                    file_path = s.upload_file(uploaded_file, base_lesson)
                    serializer.save(author=user, file=file_path)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
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
                    serializer = self.get_serializer(data=request.data)
                    serializer.is_valid(raise_exception=True)

                    uploaded_file = request.FILES["file"]
                    base_lesson = BaseLesson.objects.get(
                        homeworks=user_homework_check.user_homework.homework
                    )
                    # Загружаем файл в Selectel и получаем путь к файлу в хранилище
                    file_path = s.upload_file(uploaded_file, base_lesson)
                    serializer.save(author=user, file=file_path)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
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
        elif user.groups.filter(group__name="Admin").exists():
            base_lesson_id = request.data.get("base_lesson")

            if base_lesson_id:
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)

                uploaded_file = request.FILES["file"]
                base_lesson = BaseLesson.objects.get(id=base_lesson_id)
                # Загружаем файл в Selectel и получаем путь к файлу в хранилище
                file_path = s.upload_file(uploaded_file, base_lesson)
                serializer.save(author=user, file=file_path)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user

        if (
            user != instance.author
            and not user.groups.filter(group__name="Admin").exists()
        ):
            return Response(
                {"error": "Вы не являетесь автором этого файла"},
                status=status.HTTP_403_FORBIDDEN,
            )

        self.perform_destroy(instance)
        if s.remove_from_selectel(str(instance.file)) == "Success":
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {"error": "Ошибка удаления ресурса из хранилища Selectel"},
                status=status.HTTP_204_NO_CONTENT,
            )
