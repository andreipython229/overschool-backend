import json
from datetime import datetime, timedelta

from common_services.apply_swagger_auto_schema import apply_swagger_auto_schema
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from courses.models import (
    BaseLesson,
    Course,
    CourseCopy,
    UserHomework,
    UserHomeworkCheck,
)
from courses.models.homework.user_homework import UserHomeworkStatusChoices
from courses.models.students.students_group import StudentsGroup
from courses.paginators import UserHomeworkPagination
from courses.serializers import (
    UserHomeworkDetailSerializer,
    UserHomeworkSerializer,
    UserHomeworkStatisticsSerializer,
)
from django.core.exceptions import PermissionDenied
from django.db.models import OuterRef, Q, Subquery
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework import generics, permissions, status, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response
from schools.models import School
from schools.school_mixin import SchoolMixin
from users.models import User

from .utils import get_group_course_pairs

s3 = UploadToS3()


class UserHomeworkViewSet(WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet):
    """Эндпоинт домашних заданий ученика.\n
    <h2>/api/{school_name}/user_homeworks/</h2>\n
    Cоздавать дз может только ученик, а так же редактировать и удалять исключительно свои дз
    (свои поля-"text", "file"), учитель подкидывается исходя из группы пользователя.
    """

    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "delete", "head"]
    parser_classes = (MultiPartParser, JSONParser)

    def get_permissions(self, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if (
            user.groups.filter(group__name="Student", school=school_id).exists()
            or user.email == "student@coursehub.ru"
        ):
            return permissions
        if self.action in ["list", "retrieve"]:
            # Разрешения для просмотра домашних заданий (любой пользователь школы)
            if user.groups.filter(
                group__name__in=["Teacher", "Admin"], school=school_id
            ).exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_queryset(self, pk=None, *args, **kwargs):
        if getattr(self, "swagger_fake_view", False):
            return (
                UserHomework.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        school_name = self.kwargs.get("school_name")
        course_id = self.kwargs.get("course_id")
        school_id = School.objects.get(name=school_name).school_id
        user = self.request.user
        if course_id:
            try:
                course_id = int(course_id)
                course = Course.objects.get(course_id=course_id)
                if course.is_copy:
                    if user.groups.filter(
                        group__name="Student", school=school_id
                    ).exists():
                        return UserHomework.objects.filter(
                            user=user, copy_course_id=course_id
                        ).order_by("-created_at")
                    if user.groups.filter(
                        group__name="Teacher", school=school_id
                    ).exists():
                        return UserHomework.objects.filter(
                            teacher=user, copy_course_id=course_id
                        ).order_by("-created_at")
                    if user.groups.filter(
                        group__name="Admin", school=school_id
                    ).exists():
                        return UserHomework.objects.filter(
                            copy_course_id=course_id
                        ).order_by("-created_at")
                else:
                    if user.groups.filter(
                        group__name="Student", school=school_id
                    ).exists():
                        return UserHomework.objects.filter(
                            user=user,
                            homework__section__course__school__name=school_name,
                        ).order_by("-created_at")
                    if user.groups.filter(
                        group__name="Teacher", school=school_id
                    ).exists():
                        return UserHomework.objects.filter(
                            teacher=user,
                            homework__section__course__school__name=school_name,
                        ).order_by("-created_at")
                    if user.groups.filter(
                        group__name="Admin", school=school_id
                    ).exists():
                        return UserHomework.objects.filter(
                            homework__section__course__school__name=school_name
                        ).order_by("-created_at")
                return UserHomework.objects.none()
            except ValueError as e:
                return Response(
                    {"error": e.message},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            if user.groups.filter(group__name="Student", school=school_id).exists():
                return UserHomework.objects.filter(
                    user=user, homework__section__course__school__name=school_name
                ).order_by("-created_at")
            if user.groups.filter(group__name="Teacher", school=school_id).exists():
                return UserHomework.objects.filter(
                    teacher=user, homework__section__course__school__name=school_name
                ).order_by("-created_at")
            if user.groups.filter(group__name="Admin", school=school_id).exists():
                return UserHomework.objects.filter(
                    homework__section__course__school__name=school_name
                ).order_by("-created_at")
            return UserHomework.objects.none()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return UserHomeworkDetailSerializer
        else:
            return UserHomeworkSerializer

    def create(self, request, *args, **kwargs):
        user = request.user
        self.kwargs.get("school_name")
        course_id = self.request.data.get("course_id")
        course = Course.objects.get(course_id=course_id)
        data = request.data.copy()

        # Если курс является копией
        if course.is_copy:
            data["copy_course_id"] = data.pop("course_id", None)

            # Ищем оригинальный курс с таким же названием и is_copy=False
            original_course = CourseCopy.objects.get(course_copy_id=course.course_id)

            if original_course:
                # Ищем домашнюю работу в оригинальном курсе
                baselesson = BaseLesson.objects.get(
                    homeworks=request.data.get("homework")
                )
                teacher_group = user.students_group_fk.filter(
                    course_id=course.course_id
                ).first()
            else:
                raise NotFound("Оригинальный курс для копии не найден.")
        else:
            # Если курс не является копией, ищем домашнее в текущем курсе
            baselesson = BaseLesson.objects.get(homeworks=request.data.get("homework"))
            teacher_group = user.students_group_fk.filter(
                course_id=baselesson.section.course
            ).first()
        existing_user_homework = UserHomework.objects.filter(
            user=user, homework=request.data.get("homework")
        ).first()
        if existing_user_homework:
            return Response(
                {"status": "Error", "message": "Объект UserHomework уже существует"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group = None

        if user.groups.filter(group__name="Student").exists():
            try:
                if course.is_copy:
                    group = user.students_group_fk.get(
                        course_id=course.course_id, students=user
                    )
                else:
                    group = user.students_group_fk.get(
                        course_id=baselesson.section.course, students=user
                    )
            except Exception:
                raise NotFound("Ошибка поиска группы пользователя.")

        if group.group_settings.task_submission_lock:
            return Response(
                {
                    "status": "Error",
                    "message": "Отправлять домашки запрещено в настройках группы студентов",
                },
            )

        serializer = UserHomeworkSerializer(data=data)

        if serializer.is_valid():
            if group and group.type == "WITHOUT_TEACHER":
                # Если группа без учителя, считаем домашку сразу успешной
                serializer.save(user=user, status=UserHomeworkStatusChoices.SUCCESS)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                # В противном случае, сохраняем согласно стандартной логике
                teacher = User.objects.get(id=teacher_group.teacher_id_id)
                serializer.save(user=user, teacher=teacher)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        user_homework = self.get_object()
        user = request.user

        if user_homework.user != user:
            return Response(
                {
                    "status": "Error",
                    "message": "Пользователь может удалить только свою домашнюю работу",
                },
            )
        else:
            # Файлы текста и аудио, связанные с user_homework
            user_homework_files = list(user_homework.text_files.values("file")) + list(
                user_homework.audio_files.values("file")
            )
            # Файлы текста и аудио, связанные с user_homework_check
            user_homework_checks_files = []
            user_homework_checks = user_homework.user_homework_checks.all()
            for user_homework_check in user_homework_checks:
                user_homework_checks_files += list(
                    user_homework_check.text_files.values("file")
                ) + list(user_homework_check.audio_files.values("file"))

            files_to_delete = list(
                map(
                    lambda el: str(el["file"]),
                    user_homework_files + user_homework_checks_files,
                )
            )
            # Удаляем сразу все файлы, связанные с домашней работой пользователя и ее доработками
            objects_to_delete = [{"Key": key} for key in files_to_delete]

            remove_resp = (
                s3.delete_files(objects_to_delete) if files_to_delete else None
            )

            self.perform_destroy(user_homework)

            if remove_resp == "Error":
                return Response(
                    {"error": "Ошибка удаления ресурса из хранилища Selectel"},
                    status=status.HTTP_204_NO_CONTENT,
                )
            else:
                return Response(status=status.HTTP_204_NO_CONTENT)


class HomeworkStatisticsView(WithHeadersViewSet, SchoolMixin, generics.ListAPIView):
    """Эндпоинт домашних заданий ученика.\n
    <h2>/api/{school_name}/homeworks_stats/</h2>\n
    Для поиска по нескольким названиям групп использовать параметры group_name_{i}_{j}.
    Пример:
    /api/{school_name}/homeworks_stats/?group_name_0_1=Группа_1&group_name_0_2=Группа_2

    Для поиска по нескольким названиема групп в конкретных курсах использовать параметры
    group_name_{i}_{j} и course_name_{i}_{j}. При этом индексы как {i}, так и {j} должны сопадать
    для обоих параметров в паре.
    Пример:
    /api/{school_name}/homeworks_stats/?group_name_0_1=Группа_1&course_name_0_1=Курс_1&group_name_0_2=Группа_2&course_name_0_2=Курс_2

    Порядок следования как параметров, так и индексов в них не принципиален (можно в разнобой),
    главное, чтобы индексы соответствовали требованиям выше

    Для фильтрации одного курса для всех условий доступен парметр course_name без индексов
    Пример:
    /api/{school_name}/homeworks_stats/?course_name=Курс_1

    Для поиска по ФИО или email использовать параметр student (порядок следования ФИО, регистр и полнота текста не принципиальны)
    Пример:
    /api/{school_name}/homeworks_stats/?student=Фамилия Имя Отчество
    /api/{school_name}/homeworks_stats/?student=email
    """

    serializer_class = UserHomeworkStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = UserHomeworkPagination

    def get_permissions(self, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(
            group__name__in=["Student", "Teacher", "Admin"], school=school_id
        ).exists():
            return permissions
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_queryset(self, *args, **kwargs):
        if getattr(self, "swagger_fake_view", False):
            return (
                UserHomework.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы

        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
        user = self.request.user
        course_data = self.request.query_params.get("course_data")

        # Если course_copy_id передан, фильтруем по нему
        if course_data:
            try:
                course_ids = course_data.split(",")
                course_ids = [int(id.strip()) for id in course_ids]
            except (json.JSONDecodeError, TypeError) as e:
                raise ValidationError("Invalid course_data format")

            # Фильтрация по копиям курсов
            copied_courses_queryset = UserHomework.objects.filter(
                copy_course_id__in=course_ids,
            )

            # Фильтрация по оригинальным курсам
            original_courses_queryset = UserHomework.objects.filter(
                homework__section__course__school__name=school_name,
            )

            queryset = copied_courses_queryset | original_courses_queryset
        else:
            queryset = UserHomework.objects.filter(
                homework__section__course__school__name=school_name,
            )

        # Дополнительные фильтры по ролям пользователей
        if user.groups.filter(group__name="Student", school=school_id).exists():
            queryset = queryset.filter(user=user)
        elif user.groups.filter(group__name="Teacher", school=school_id).exists():
            queryset = queryset.filter(teacher=user)
        elif user.groups.filter(group__name="Admin", school=school_id).exists():
            pass

        if self.request.GET.get("teacher_id"):
            queryset = queryset.filter(teacher_id=self.request.GET.get("teacher_id"))
        if self.request.GET.get("status"):
            queryset = queryset.filter(status=self.request.GET.get("status"))

        if self.request.GET.get("start_mark"):
            queryset = queryset.filter(mark__gte=self.request.GET.get("start_mark"))

        if self.request.GET.get("end_mark"):
            queryset = queryset.filter(mark__lte=self.request.GET.get("end_mark"))

        if self.request.GET.get("mark"):
            queryset = queryset.filter(mark=self.request.GET.get("mark"))

        if self.request.GET.get("course_name"):
            queryset = queryset.filter(
                homework__section__course__name=self.request.GET.get("course_name")
            )

        if self.request.GET.get("homework_name"):
            queryset = queryset.filter(
                homework__name__icontains=self.request.GET.get("homework_name")
            )

        # поиск по email и ФИО (ФИО)
        if self.request.GET.get("student"):
            query_param = self.request.GET.get("student")
            # Разделение строки поиска на отдельные слова
            # Срезали лишние элементы, чтобы база не одурела от поиска
            search_terms = query_param.split()[:3]

            # Создание Q-объекта для накопления условий фильтрации
            search_filter = Q()

            # Построение фильтра для каждого слова
            for term in search_terms:
                search_filter |= Q(user__last_name__icontains=term)
                search_filter |= Q(user__first_name__icontains=term)
                search_filter |= Q(user__email__icontains=term)

            # Применение фильтрации к QuerySet
            queryset = queryset.filter(search_filter)

        # фильтруем по group_name_{i} и course_name_{i}
        group_course_pairs = get_group_course_pairs(self.request.GET)
        if group_course_pairs:
            # Создаем список Q-объектов для каждой пары (group_name, course_name), фильтруя по принадлежности к группе и имени курса.
            queries = []
            for group, course in group_course_pairs:
                # Если в паре group course есть course
                if course:
                    query = Q(
                        teacher_id__in=StudentsGroup.objects.filter(
                            name=group
                        ).values_list("teacher_id", flat=True),
                        homework__section__course__name=course,
                    )
                # Если в паре group course нет course
                else:
                    query = Q(
                        teacher_id__in=StudentsGroup.objects.filter(
                            name=group
                        ).values_list("teacher_id", flat=True)
                    )
                queries.append(query)

            # Извлекаем первый элемент списка для объединения.
            combined_query = queries.pop()

            # Объединяем остальные Q-объекты с помощью оператора | (OR).
            for query in queries:
                combined_query |= query

            # Применяем объединенный запрос к queryset для фильтрации записей.
            queryset = queryset.filter(combined_query)

        if self.request.GET.get("start_date"):
            start_datetime = timezone.make_aware(
                datetime.strptime(self.request.GET.get("start_date"), "%Y-%m-%d")
            )
            subquery = UserHomeworkCheck.objects.filter(
                user_homework=OuterRef("pk")
            ).order_by("-updated_at")[:1]
            queryset = queryset.annotate(
                last_check_updated_at=Subquery(subquery.values("updated_at"))
            )
            queryset = queryset.filter(last_check_updated_at__gte=start_datetime)

        if self.request.GET.get("end_date"):
            end_datetime = timezone.make_aware(
                datetime.strptime(self.request.GET.get("end_date"), "%Y-%m-%d")
                + timedelta(days=1)
                - timedelta(seconds=1)
            )
            subquery = UserHomeworkCheck.objects.filter(
                user_homework=OuterRef("pk")
            ).order_by("-updated_at")[:1]
            queryset = queryset.annotate(
                last_check_updated_at=Subquery(subquery.values("updated_at"))
            )
            queryset = queryset.filter(last_check_updated_at__lte=end_datetime)
        return queryset

    @action(detail=False, methods=["get"], url_path="teachers", url_name="teachers")
    def list_teachers(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school = get_object_or_404(School, name=school_name)

        teachers = User.objects.filter(
            groups__group__name="Teacher",
            groups__school=school.school_id
        ).distinct()

        data = [
            {
                "id": teacher.id,
                "name": f"{teacher.last_name} {teacher.first_name}".strip(),
                "email": teacher.email,
            }
            for teacher in teachers
        ]

        return Response(data)


UserHomeworkViewSet = apply_swagger_auto_schema(
    tags=[
        "homeworks",
    ]
)(UserHomeworkViewSet)
HomeworkStatisticsView = apply_swagger_auto_schema(
    tags=[
        "homeworks",
    ]
)(HomeworkStatisticsView)
