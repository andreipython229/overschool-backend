from datetime import datetime

import yadisk
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.models import TextFile
from common_services.serializers import TextFileSerializer

# from courses.models.homework.user_homework import UserHomework
from courses.models import BaseLesson, UserHomework
from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response

from overschool import settings


def upload_to_yandex(uploaded_file, base_lesson):
    y = yadisk.YaDisk(token=settings.YANDEX_TOKEN)
    course = base_lesson.section.course
    course_id = course.course_id
    # school_id = course.school.school_id
    file_path = "/{}_course/{}_lesson/{}_{}".format(
        course_id, base_lesson.id, datetime.now(), uploaded_file.name
    )
    # file_path = "/{}_school/{}_course/{}_lesson/{}_{}".format(school_id, course_id, base_lesson.id, datetime.now(), uploaded_file.name)
    try:
        y.upload(uploaded_file, file_path)
    except yadisk.exceptions.ConflictError:
        # if y.exists("/{}_school/{}_course".format(school_id, course_id)):
        #     y.mkdir("/{}_school/{}_course/{}_lesson".format(school_id, course_id, base_lesson.id))
        # elif y.exists("/{}_school".format(school_id)):
        #     y.mkdir("/{}_school/{}_course".format(school_id, course_id))
        #     y.mkdir("/{}_school/{}_course/{}_lesson".format(school_id, course_id, base_lesson.id))
        # else:
        #     y.mkdir("/{}_school".format(school_id))
        #     y.mkdir("/{}_school/{}_course".format(school_id, course_id))
        #     y.mkdir("/{}_school/{}_course/{}_lesson".format(school_id, course_id, base_lesson.id))

        if y.exists("/{}_course".format(course_id)):
            y.mkdir("/{}_course/{}_lesson".format(course_id, base_lesson.id))
        else:
            y.mkdir("/{}_course".format(course_id))
            y.mkdir("/{}_course/{}_lesson".format(course_id, base_lesson.id))
        y.upload(uploaded_file, file_path)
    return file_path


class TextFileViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    """
    Модель добавления текстовых к занятиям
    """

    queryset = TextFile.objects.all()
    serializer_class = TextFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["post", "delete", "head"]

    def create(self, request, *args, **kwargs):
        user = request.user

        # Проверяем, что пользователь студент
        if user.groups.filter(name="Student").exists():
            user_homework_id = request.data.get("user_homework")

            if user_homework_id:
                # Проверяем, что пользователь является автором указанной домашней работы
                user_homework = UserHomework.objects.filter(
                    user_homework_id=user_homework_id, user=user
                ).first()
                # if not user_homework:
                #     return Response(
                #         {"error": "Объект не найден"}, status=status.HTTP_404_NOT_FOUND
                #     )
                if user_homework:
                    serializer = self.get_serializer(data=request.data)
                    serializer.is_valid(raise_exception=True)

                    uploaded_file = request.FILES["file"]
                    base_lesson = BaseLesson.objects.get(
                        homeworks=user_homework.homework
                    )
                    # Загружаем файл на Яндекс.Диск и получаем путь к файлу на диске
                    file_path = upload_to_yandex(uploaded_file, base_lesson)
                    serializer.save(author=user, file=file_path)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)

                else:
                    return Response(
                        {
                            "error": "Пользователь не является автором указанной домашней работы"
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

            else:
                return Response(
                    {
                        "error": "Не указан идентификатор домашней работы (user_homework) или базового урока ("
                        "base_lesson)"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Проверяем, что пользователь админ
        elif user.groups.filter(name="Admin").exists():
            base_lesson_id = request.data.get("base_lesson")

            if base_lesson_id:
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)

                uploaded_file = request.FILES["file"]
                # base_lesson = BaseLesson.objects.filter(Q(lessons=base_lesson_id) | Q(homeworks=base_lesson_id) | Q(tests=base_lesson_id)).first()
                base_lesson = BaseLesson.objects.get(id=base_lesson_id)
                # Загружаем файл на Яндекс.Диск и получаем путь к файлу на диске
                file_path = upload_to_yandex(uploaded_file, base_lesson)
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

        if user != instance.author and not user.groups.filter(name="Admin").exists():
            return Response(
                {"error": "Вы не являетесь автором этого файла"},
                status=status.HTTP_403_FORBIDDEN,
            )
        y = yadisk.YaDisk(token=TOKEN)
        y.remove(str(instance.file), permanently=True)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
