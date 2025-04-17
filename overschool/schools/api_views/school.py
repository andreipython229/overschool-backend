import re
import traceback
from datetime import datetime, timedelta

import pytz
from chats.models import UserChat
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from courses.models import (
    Homework,
    Lesson,
    Section,
    SectionTest,
    StudentsGroup,
    TrainingDuration,
    UserHomework,
    UserProgressLogs,
)
from courses.models.common.base_lesson import BaseLesson, LessonAvailability
from courses.models.students.students_history import StudentsHistory
from courses.paginators import StudentsPagination
from courses.services import get_student_progress, progress_subquery
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Avg, Count, F, OuterRef, Prefetch, Q, Subquery, Sum
from django.http import HttpResponse
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from schools.models import (
    ProdamusPaymentLink,
    School,
    SchoolDocuments,
    SchoolExpressPayLink,
    SchoolHeader,
    SchoolPaymentMethod,
    SchoolStudentsTableSettings,
    SchoolTask,
    Tariff,
    TariffPlan,
)
from schools.school_mixin import SchoolMixin
from schools.serializers import (
    ProdamusLinkSerializer,
    SchoolExpressPayLinkSerializer,
    SchoolGetSerializer,
    SchoolPaymentMethodSerializer,
    SchoolSerializer,
    SchoolStudentsTableSettingsSerializer,
    SchoolTaskSummarySerializer,
    SchoolUpdateSerializer,
    TariffSerializer,
)
from schools.services import Hmac
from users.models import Profile, UserGroup, UserRole

s3 = UploadToS3()


class SchoolViewSet(WithHeadersViewSet, viewsets.ModelViewSet):
    """Эндпоинт на получение, создания, изменения и удаления школ \n
    <h2>/api/{school_name}/schools/</h2>\n
    Разрешения для просмотра школ (любой пользователь)\n
    Разрешения для создания и изменения школы (только пользователи зарегистрированные указавшие email и phone_number')"""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return SchoolGetSerializer
        if self.action in ["update", "partial_update"]:
            return SchoolUpdateSerializer
        else:
            return SchoolSerializer

    def get_permissions(self):

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin").exists():
            return permissions
        if user.is_authenticated and self.action in ["create"]:
            return permissions
        if (
            self.action in ["stats", "section_student"]
            and user.groups.filter(group__name__in=["Teacher", "Admin"]).exists()
        ):
            return permissions
        if self.action in ["list", "retrieve", "create"]:
            # Разрешения для просмотра домашних заданий (любой пользователь школы)
            if (
                user.groups.filter(group__name__in=["Teacher", "Student"]).exists()
                or user.email == "student@coursehub.ru"
            ):
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_queryset(self, *args, **kwargs):
        if getattr(self, "swagger_fake_view", False):
            return (
                School.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        user = self.request.user
        queryset = School.objects.filter(groups__user=user).distinct()
        return queryset

    def create(self, request, *args, **kwargs):
        User = get_user_model()
        admin_user = User.objects.get(email="admin@coursehub.ru")
        teacher_user = User.objects.get(email="teacher@coursehub.ru")
        group_admin = UserRole.objects.get(name="Admin")
        group_teacher = UserRole.objects.get(name="Teacher")

        if not request.user.email or not request.user.phone_number:
            raise PermissionDenied("Email и phone number пользователя обязательны.")
        # Проверка количества школ, которыми владеет пользователь
        if School.objects.filter(owner=request.user).count() >= 2:
            raise PermissionDenied(
                "Пользователь может быть владельцем только двух школ."
            )

        # Добавление пользователей во все школы
        try:
            with transaction.atomic():
                schools = School.objects.all()
                for school in schools:
                    if not UserGroup.objects.filter(
                        user=admin_user, group=group_admin, school=school
                    ).exists():
                        UserGroup.objects.create(
                            user=admin_user, group=group_admin, school=school
                        )

                    if not UserGroup.objects.filter(
                        user=teacher_user, group=group_teacher, school=school
                    ).exists():
                        UserGroup.objects.create(
                            user=teacher_user, group=group_teacher, school=school
                        )
        except User.DoesNotExist:
            return HttpResponse("Пользователь не найден.", status=400)
        except Exception as e:
            return HttpResponse(f"Произошла ошибка: {str(e)}", status=500)

        serializer = SchoolSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if School.objects.filter(name=serializer.validated_data["name"]).exists():
            return HttpResponse("Название школы уже существует.", status=400)

        school = serializer.save(
            owner=request.user,
            tariff=Tariff.objects.get(name=TariffPlan.JUNIOR.value),
            used_trial=True,
            trial_end_date=timezone.now() + timezone.timedelta(days=14),
        )
        if school:
            SchoolHeader.objects.create(school=school, name=school.name)
            SchoolDocuments.objects.create(school=school, user=request.user)

        # Создание записи в модели UserGroup для добавления пользователя в качестве администратора
        user_group = UserGroup(user=request.user, group=group_admin, school=school)
        user_group.save()

        # Добавление admin@coursehub.ru как администратора школы
        try:
            admin_user = User.objects.get(email="admin@coursehub.ru")
            UserGroup.objects.create(user=admin_user, group=group_admin, school=school)
        except User.DoesNotExist:
            return HttpResponse(
                "Пользователь с email admin@coursehub.ru не найден.", status=400
            )

        # Добавление teacher@coursehub.ru как учителя школы
        try:
            teacher_user = User.objects.get(email="teacher@coursehub.ru")
            group_teacher = UserRole.objects.get(name="Teacher")
            UserGroup.objects.create(
                user=teacher_user, group=group_teacher, school=school
            )
        except User.DoesNotExist:
            return HttpResponse(
                "Пользователь с email teacher@coursehub.ru не найден.", status=400
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        school = self.get_object()
        user = self.request.user
        if not user.groups.filter(group__name="Admin", school=school).exists():
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

        serializer = SchoolUpdateSerializer(school, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        name_data = serializer.validated_data.get("name")

        if name_data:
            existing_school = (
                School.objects.filter(name=name_data).exclude(pk=school.pk).first()
            )
            if existing_school:
                return Response(
                    "Название школы уже существует.", status=status.HTTP_400_BAD_REQUEST
                )
        platform_logo = request.FILES.get("branding.platform_logo")
        if platform_logo:
            if school.branding.platform_logo:
                s3.delete_file(str(school.branding.platform_logo))
            logo_url = s3.upload_school_image(platform_logo, school.school_id)
            school.branding.platform_logo = logo_url
            school.branding.save()

        self.perform_update(serializer)
        serializer = SchoolGetSerializer(school)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.owner != request.user:
            raise PermissionDenied("У вас нет разрешения на удаление этой школы.")

        # Получаем список файлов, хранящихся в папке удаляемой школы
        files_to_delete = s3.get_list_objects("{}_school".format(instance.pk))
        # Удаляем все файлы и сегменты, связанные с удаляемой школой
        remove_resp = None
        if files_to_delete:
            if s3.delete_files(files_to_delete) == "Error":
                remove_resp = "Error"

        self.perform_destroy(instance)

        if remove_resp == "Error":
            return Response(
                {"error": "Ошибка удаления ресурса из хранилища Selectel"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def get_student_sections_and_availability(self, student_id, student_groups):
        """
        Метод для получения секций, уроков и их доступности для студента.
        """
        student_data = []
        if not student_groups:
            return student_data

        group_ids = [group.group_id for group in student_groups]

        course_ids = {group.course_id_id for group in student_groups}

        # 1. Получаем информацию о длительности обучения
        training_durations = {
            td.students_group_id: td
            for td in TrainingDuration.objects.filter(
                students_group_id__in=group_ids, user_id=student_id
            )
        }

        # 2. Загружаем все нужные секции одним запросом, сортируем по курсу и порядку секций
        all_sections = (
            Section.objects.filter(course_id__in=course_ids)
            .order_by("course_id", "order")
            .prefetch_related(
                Prefetch(
                    "lessons",
                    queryset=BaseLesson.objects.order_by("order"),
                    to_attr="ordered_lessons",
                )
            )
        )

        # Группируем секции по курсам
        sections_by_course = {}
        for section in all_sections:
            if section.course_id not in sections_by_course:
                sections_by_course[section.course_id] = []
            sections_by_course[section.course_id].append(section)

        # 3. Получаем все ID уроков из загруженных секций
        lesson_ids = set()
        for section in all_sections:
            for lesson in section.ordered_lessons:
                lesson_ids.add(lesson.id)

        if not lesson_ids:
            for group in student_groups:
                group_data = self._prepare_group_data(
                    group, training_durations, sections_by_course, {}, {}, {}, {}
                )
                student_data.append(group_data)
            return student_data

        # 4. Получаем все уроки (только нужные поля) одним запросом
        lesson_map = {
            lesson["id"]: lesson
            for lesson in BaseLesson.objects.filter(id__in=lesson_ids).values(
                "id", "name", "active", "order"
            )
        }

        # 5. Определяем типы уроков
        lesson_types = {lesson_id: "unknown" for lesson_id in lesson_ids}
        lesson_types.update(
            {
                lesson_id: "homework"
                for lesson_id in Homework.objects.filter(
                    baselesson_ptr_id__in=lesson_ids
                ).values_list("baselesson_ptr_id", flat=True)
            }
        )
        lesson_types.update(
            {
                lesson_id: "lesson"
                for lesson_id in Lesson.objects.filter(
                    baselesson_ptr_id__in=lesson_ids
                ).values_list("baselesson_ptr_id", flat=True)
            }
        )
        lesson_types.update(
            {
                lesson_id: "test"
                for lesson_id in SectionTest.objects.filter(
                    baselesson_ptr_id__in=lesson_ids
                ).values_list("baselesson_ptr_id", flat=True)
            }
        )

        # 6. Прогресс пользователя одним запросом
        user_logs = {
            log.lesson_id: log
            for log in UserProgressLogs.objects.filter(
                user_id=student_id, lesson_id__in=lesson_ids
            )
        }

        # 7. Домашние работы пользователя одним запросом
        user_homeworks = {
            hw.homework.baselesson_ptr_id: hw
            for hw in UserHomework.objects.filter(
                user_id=student_id, homework__baselesson_ptr_id__in=lesson_ids
            ).select_related("homework")
        }

        # 8. Доступность уроков для студента одним запросом (1 запрос)
        lesson_availabilities = {
            avail.lesson_id: avail.available
            for avail in LessonAvailability.objects.filter(
                student_id=student_id, lesson_id__in=lesson_ids
            ).only("lesson_id", "available")
        }

        # 9. Обрабатываем группы и формируем результат
        for group in student_groups:
            group_data = self._prepare_group_data(
                group,
                training_durations,
                sections_by_course,
                lesson_map,
                lesson_types,
                user_logs,
                user_homeworks,
                lesson_availabilities,
            )
            student_data.append(group_data)

        return student_data

    def _prepare_group_data(
        self,
        group,
        training_durations,
        sections_by_course,
        lesson_map,
        lesson_types,
        user_logs,
        user_homeworks,
        lesson_availabilities,
    ):
        """Вспомогательный метод для формирования данных группы."""
        remaining_period = None
        td = training_durations.get(group.group_id)

        if td:
            limit = td.limit
            if limit and limit > 0:
                past_period = (timezone.now() - td.created_at).days
                remaining_period = max(limit - past_period, 0)

        elif group.training_duration > 0:
            remaining_period = group.training_duration

        group_data = {
            "group_id": group.group_id,
            "remaining_period": remaining_period,
            "sections": [],
        }

        course_id = group.course_id_id
        sections = sections_by_course.get(course_id, [])

        for section in sections:
            lessons_data = []

            for lesson in section.ordered_lessons:
                lesson_id = lesson.id
                if lesson_id not in lesson_map:
                    continue

                obj_type = lesson_types.get(lesson_id, "unknown")

                availability = lesson_availabilities.get(lesson_id, True)

                status, mark = None, None
                if availability:
                    log = user_logs.get(lesson_id)
                    if log:

                        status = "Пройдено" if log.completed else "Не пройдено"
                        mark = None

                        if obj_type == "homework" and not log.completed:
                            user_homework = user_homeworks.get(lesson_id)
                            if user_homework:
                                status = user_homework.status
                                mark = user_homework.mark

                    else:
                        status = "Не пройдено"
                        mark = None

                        if obj_type == "homework":
                            user_homework = user_homeworks.get(lesson_id)
                            if user_homework:
                                status = user_homework.status
                                mark = user_homework.mark

                lessons_data.append(
                    {
                        "lesson_id": lesson_id,
                        "type": obj_type,
                        "name": lesson_map[lesson_id]["name"],
                        "availability": availability,
                        "active": lesson_map[lesson_id]["active"],
                        "status": status,
                        "mark": mark,
                    }
                )

            group_data["sections"].append(
                {
                    "section_id": section.section_id,
                    "name": section.name,
                    "lessons": lessons_data,
                }
            )

        return group_data

    @action(detail=True, methods=["get"])
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "student_id",
                openapi.IN_QUERY,
                description="ID студента",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        operation_description="Получение структуры курсов, секций и уроков для студента с указанием доступности и прогресса.",
        responses={
            200: openapi.Response(
                "Успешный ответ", schema=openapi.Schema(type=openapi.TYPE_OBJECT)
            )
        },  # Пример схемы ответа
    )
    def section_student(self, request, pk=None, *args, **kwargs):
        try:
            school_id = int(pk)
            school = School.objects.get(pk=school_id)
        except (ValueError, School.DoesNotExist):
            return Response(
                {"error": "Школа не найдена"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": "Ошибка получения данных школы"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        user = self.request.user
        student_id_str = request.query_params.get("student_id", None)

        if not student_id_str:
            return Response(
                {"error": "Не указан обязательный параметр 'student_id'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            student_id = int(student_id_str)
        except ValueError:
            return Response(
                {"error": "Параметр 'student_id' должен быть целым числом"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student_groups_query = StudentsGroup.objects.filter(
            course_id__school=school, students__id=student_id
        ).select_related("course_id")

        is_admin = user.groups.filter(group__name="Admin", school=school).exists()
        is_teacher = user.groups.filter(group__name="Teacher", school=school).exists()

        if not is_admin:
            if is_teacher:
                student_groups_query = student_groups_query.filter(teacher_id=user)
            elif user.pk == student_id:
                pass
            else:
                return Response(
                    {
                        "school_name": school.name,
                        "student_id": student_id,
                        "student_data": [],
                    },
                    status=status.HTTP_200_OK,
                )

        student_groups = list(student_groups_query)

        student_data = self.get_student_sections_and_availability(
            student_id, student_groups
        )

        response_data = {
            "school_name": school.name,
            "student_id": student_id,
            "student_data": student_data,
        }
        return Response(response_data, status=status.HTTP_200_OK)

    @action(detail=True)
    def stats(self, request, pk, *args, **kwargs):
        queryset = StudentsGroup.objects.none()
        user = self.request.user
        school = self.get_object()
        fields = self.request.GET.getlist("fields")
        sort_by = request.GET.get("sort_by", "date_added")
        sort_order = request.GET.get("sort_order", "desc")
        default_date = datetime(2023, 11, 1, tzinfo=pytz.UTC)

        if user.groups.filter(group__name="Teacher", school=school).exists():
            queryset = StudentsGroup.objects.filter(
                teacher_id=request.user, course_id__school=school
            )
        if user.groups.filter(group__name="Admin", school=school).exists():
            queryset = StudentsGroup.objects.filter(course_id__school=school)

        all_active_students = queryset.aggregate(total_users_count=Count("students"))[
            "total_users_count"
        ]

        deleted_history_queryset = StudentsHistory.objects.none()

        hide_deleted = self.request.GET.get("hide_deleted")
        if not hide_deleted:
            deleted_history_queryset = StudentsHistory.objects.filter(
                students_group_id__course_id__school=school, is_deleted=True
            )

        # Поиск
        search_value = self.request.GET.get("search_value")
        if search_value:
            cleaned_phone = re.sub(r"\D", "", search_value)

            query = (
                Q(students__first_name__icontains=search_value)
                | Q(students__last_name__icontains=search_value)
                | Q(name__icontains=search_value)
                | Q(course_id__name__icontains=search_value)
            )

            if cleaned_phone:
                query |= Q(students__phone_number__icontains=cleaned_phone)

            # Регулярное выражение для проверки email
            email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"

            # Проверяем, является ли search_value email
            if re.match(email_regex, search_value):
                queryset = queryset.filter(Q(students__email__icontains=search_value))
            else:
                queryset = queryset.filter(query)

            deleted_history_query = (
                Q(user_id__first_name__icontains=search_value)
                | Q(user_id__last_name__icontains=search_value)
                | Q(students_group_id__name__icontains=search_value)
                | Q(students_group_id__course_id__name__icontains=search_value)
            )

            if cleaned_phone:
                deleted_history_query |= Q(
                    user_id__phone_number__icontains=cleaned_phone
                )
            # Регулярное выражение для проверки email
            email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"

            # Проверяем, является ли search_value email
            if re.match(email_regex, search_value):
                deleted_history_queryset = deleted_history_queryset.filter(
                    Q(user_id__email__icontains=search_value)
                )
            else:
                deleted_history_queryset = deleted_history_queryset.filter(
                    deleted_history_query
                )
        # Фильтры
        first_name = self.request.GET.get("first_name")
        if first_name:
            queryset = queryset.filter(students__first_name=first_name).distinct()
            deleted_history_queryset = deleted_history_queryset.filter(
                user__first_name=first_name
            ).distinct()
        last_name = self.request.GET.get("last_name")
        if last_name:
            queryset = queryset.filter(students__last_name=last_name).distinct()
            deleted_history_queryset = deleted_history_queryset.filter(
                user__last_name=last_name
            ).distinct()
        course_name = self.request.GET.get("course_name")
        if course_name:
            queryset = queryset.filter(course_id__name=course_name).distinct()
            deleted_history_queryset = deleted_history_queryset.filter(
                students_group_id__course_id__name=course_name
            ).distinct()
        group_name = self.request.GET.get("group_name")
        if group_name:
            queryset = queryset.filter(name=group_name).distinct()
            deleted_history_queryset = deleted_history_queryset.filter(
                students_group_id__name=group_name
            ).distinct()
        last_active_min = self.request.GET.get("last_active_min")
        if last_active_min:
            last_active_min = datetime.strptime(last_active_min, "%Y-%m-%d")
            queryset = queryset.filter(
                students__last_login__gte=last_active_min
            ).distinct()
            deleted_history_queryset = deleted_history_queryset.filter(
                user__last_login__gte=last_active_min
            ).distinct()
        last_active_max = self.request.GET.get("last_active_max")
        if last_active_max:
            last_active_max = datetime.strptime(last_active_max, "%Y-%m-%d")
            last_active_max += timedelta(days=1)
            queryset = queryset.filter(
                students__last_login__lte=last_active_max
            ).distinct()
            deleted_history_queryset = deleted_history_queryset.filter(
                user__last_login__lte=last_active_max
            ).distinct()
        last_active = self.request.GET.get("last_active")
        if last_active:
            last_active = datetime.strptime(last_active, "%Y-%m-%d")
            queryset = queryset.filter(students__last_login=last_active).distinct()
            deleted_history_queryset = deleted_history_queryset.filter(
                user__last_login=last_active
            ).distinct()
        mark_sum = self.request.GET.get("mark_sum")
        if mark_sum:
            queryset = queryset.annotate(mark_sum=Sum("students__user_homeworks__mark"))
            queryset = queryset.filter(mark_sum__exact=mark_sum)
            deleted_history_queryset = deleted_history_queryset.annotate(
                mark_sum=Sum("user__user_homeworks__mark")
            )
            deleted_history_queryset = deleted_history_queryset.filter(
                mark_sum__exact=mark_sum
            )

        average_mark = self.request.GET.get("average_mark")
        if average_mark:
            queryset = queryset.annotate(
                average_mark=Avg("students__user_homeworks__mark")
            )
            queryset = queryset.filter(average_mark__exact=average_mark)
            deleted_history_queryset = deleted_history_queryset.annotate(
                average_mark=Avg("students__user_homeworks__mark")
            )
            deleted_history_queryset = deleted_history_queryset.filter(
                average_mark__exact=average_mark
            )
        mark_sum_min = self.request.GET.get("mark_sum_min")
        if mark_sum_min:
            queryset = queryset.annotate(mark_sum=Sum("students__user_homeworks__mark"))
            queryset = queryset.filter(mark_sum__gte=mark_sum_min)
        mark_sum_max = self.request.GET.get("mark_sum_max")
        if mark_sum_max:
            queryset = queryset.annotate(mark_sum=Sum("students__user_homeworks__mark"))
            queryset = queryset.filter(mark_sum__lte=mark_sum_max)
        average_mark_min = self.request.GET.get("average_mark_min")
        if average_mark_min:
            queryset = queryset.annotate(
                average_mark=Avg("students__user_homeworks__mark")
            )
            queryset = queryset.filter(average_mark__gte=average_mark_min)
        average_mark_max = self.request.GET.get("average_mark_max")
        if average_mark_max:
            queryset = queryset.annotate(
                average_mark=Avg("students__user_homeworks__mark")
            )
            queryset = queryset.filter(average_mark__lte=average_mark_max)

        subquery_mark_sum = (
            UserHomework.objects.filter(user_id=OuterRef("students__id"))
            .values("user_id")
            .annotate(mark_sum=Sum("mark"))
            .values("mark_sum")
        )

        subquery_average_mark = (
            UserHomework.objects.filter(user_id=OuterRef("students__id"))
            .values("user_id")
            .annotate(avg=Avg("mark"))
            .values("avg")
        )

        subquery_date_added = (
            StudentsHistory.objects.filter(
                user_id=OuterRef("students__id"),
                students_group=OuterRef("group_id"),
            )
            .order_by("-date_added")
            .values("date_added")[:1]
        )

        subquery_date_removed = (
            StudentsHistory.objects.none()
            .order_by("-date_removed")
            .values("date_removed")[:1]
        )

        subquery_mark_sum_deleted = (
            UserHomework.objects.filter(user_id=OuterRef("user_id"))
            .values("user_id")
            .annotate(mark_sum=Sum("mark"))
            .values("mark_sum")
        )

        subquery_average_mark_deleted = (
            UserHomework.objects.filter(user_id=OuterRef("user_id"))
            .values("user_id")
            .annotate(avg=Avg("mark"))
            .values("avg")
        )

        data = queryset.values(
            "course_id",
            "course_id__name",
            "group_id",
            "students__date_joined",
            "students__last_login",
            "students__email",
            "students__phone_number",
            "students__first_name",
            "students__id",
            "students__profile__avatar",
            "students__last_name",
            "name",
        ).annotate(
            mark_sum=Subquery(subquery_mark_sum),
            average_mark=Subquery(subquery_average_mark),
            date_added_student=Subquery(subquery_date_added),
            date_removed_student=Subquery(subquery_date_removed),
        )

        combined_data = data
        if not hide_deleted:
            data_deleted = deleted_history_queryset.values(
                course_id=F("students_group_id__course_id"),
                course_id__name=F("students_group_id__course_id__name"),
                group_id=F("students_group_id"),
                students__date_joined=F("user_id__date_joined"),
                students__last_login=F("user_id__last_login"),
                students__email=F("user_id__email"),
                students__phone_number=F("user_id__phone_number"),
                students__first_name=F("user_id__first_name"),
                students__id=F("user_id"),
                students__profile__avatar=F("user_id__profile__avatar"),
                students__last_name=F("user_id__last_name"),
                name=F("students_group_id__name"),
                mark_sum=Subquery(subquery_mark_sum_deleted),
                average_mark=Subquery(subquery_average_mark_deleted),
                date_added_student=F("date_added"),
                date_removed_student=F("date_removed"),
            )

            # Объединение двух QuerySet
            combined_data = data.union(data_deleted)

        filtered_active_students = combined_data.count()

        if sort_by == "progress":
            for obj in combined_data:
                user_id = obj.get("students__id")
                course_id = obj.get("course_id")

                if user_id and course_id:
                    progress = progress_subquery(user_id, course_id)
                else:
                    progress = None

                obj["progress"] = progress

        # Сортировка
        if sort_by in [
            "students__last_name",
            "last_name",
            "students__email",
            "name",
            "course_id__name",
            "date_added_student",
            "date_removed_student",
            "progress",
            "average_mark",
            "mark_sum",
            "students__date_joined",
        ]:
            if sort_order == "asc":
                if sort_by in [
                    "date_added_student",
                    "date_removed_student",
                    "students__date_joined",
                ]:
                    sorted_data = sorted(
                        combined_data,
                        key=lambda x: x.get(sort_by, datetime.min)
                        if x.get(sort_by) is not None
                        else default_date,
                    )
                elif sort_by in [
                    "progress",
                    "average_mark",
                    "mark_sum",
                ]:
                    sorted_data = sorted(
                        combined_data,
                        key=lambda x: x.get(sort_by, 0)
                        if x.get(sort_by) is not None
                        else 0,
                    )
                else:
                    sorted_data = sorted(
                        combined_data,
                        key=lambda x: str(x.get(sort_by, "") or "").lower(),
                    )

            else:
                if sort_by in ["date_added", "date_removed", "last_active"]:
                    sorted_data = sorted(
                        combined_data,
                        key=lambda x: x.get(sort_by, datetime.min)
                        if x.get(sort_by) is not None
                        else default_date,
                        reverse=True,
                    )
                elif sort_by in [
                    "progress",
                    "average_mark",
                    "mark_sum",
                ]:
                    sorted_data = sorted(
                        combined_data,
                        key=lambda x: x.get(sort_by, 0)
                        if x.get(sort_by) is not None
                        else 0,
                        reverse=True,
                    )
                else:
                    sorted_data = sorted(
                        combined_data,
                        key=lambda x: str(x.get(sort_by, "") or "").lower(),
                        reverse=True,
                    )

            unique_students_count = queryset.aggregate(
                unique_students_count=Count("students", distinct=True)
            )["unique_students_count"]

            paginator = StudentsPagination()
            paginated_data = paginator.paginate_queryset(sorted_data, request)
            serialized_data = []
            for item in paginated_data:
                if not item["students__id"]:
                    continue
                if "Прогресс" in fields and sort_by != "progress":
                    student_group = StudentsGroup.objects.filter(
                        students__id=item["students__id"], course_id=item["course_id"]
                    ).first()
                    if student_group:
                        serialized_data.append(
                            {
                                "course_id": item["course_id"],
                                "course_name": item["course_id__name"],
                                "group_id": item["group_id"],
                                "last_active": item["students__date_joined"],
                                "last_login": item["students__last_login"],
                                "email": item["students__email"],
                                "phone_number": item["students__phone_number"],
                                "first_name": item["students__first_name"],
                                "student_id": item["students__id"],
                                "avatar": s3.get_link(item["students__profile__avatar"])
                                if item["students__profile__avatar"]
                                else s3.get_link("users/avatars/base_avatar.jpg"),
                                "last_name": item["students__last_name"],
                                "group_name": item["name"],
                                "school_name": school.name,
                                "mark_sum": item["mark_sum"],
                                "average_mark": item["average_mark"],
                                "date_added": item["date_added_student"],
                                "date_removed": item["date_removed_student"],
                                "is_deleted": True
                                if item["date_removed_student"] is not None
                                else False,
                                "progress": progress_subquery(
                                    item["students__id"], item["course_id"]
                                ),
                                "all_active_students": all_active_students,
                                "unique_students_count": unique_students_count,
                                "filtered_active_students": filtered_active_students,
                                "chat_uuid": UserChat.get_existed_chat_id_by_type(
                                    chat_creator=user,
                                    reciever=item["students__id"],
                                    type="PERSONAL",
                                ),
                            }
                        )
                    else:
                        serialized_data.append(
                            {
                                "course_id": item["course_id"],
                                "course_name": item["course_id__name"],
                                "group_id": item["group_id"],
                                "last_active": item["students__date_joined"],
                                "last_login": item["students__last_login"],
                                "email": item["students__email"],
                                "phone_number": item["students__phone_number"],
                                "first_name": item["students__first_name"],
                                "student_id": item["students__id"],
                                "avatar": s3.get_link(item["students__profile__avatar"])
                                if item["students__profile__avatar"]
                                else s3.get_link("users/avatars/base_avatar.jpg"),
                                "last_name": item["students__last_name"],
                                "group_name": item["name"],
                                "school_name": school.name,
                                "mark_sum": item["mark_sum"],
                                "average_mark": item["average_mark"],
                                "date_added": item["date_added_student"],
                                "date_removed": item["date_removed_student"],
                                "is_deleted": True
                                if item["date_removed_student"] is not None
                                else False,
                                "progress": 0,
                                "all_active_students": all_active_students,
                                "unique_students_count": unique_students_count,
                                "filtered_active_students": filtered_active_students,
                                "chat_uuid": UserChat.get_existed_chat_id_by_type(
                                    chat_creator=user,
                                    reciever=item["students__id"],
                                    type="PERSONAL",
                                ),
                            }
                        )
                elif sort_by == "progress":
                    serialized_data.append(
                        {
                            "course_id": item["course_id"],
                            "course_name": item["course_id__name"],
                            "group_id": item["group_id"],
                            "last_active": item["students__date_joined"],
                            "last_login": item["students__last_login"],
                            "email": item["students__email"],
                            "phone_number": item["students__phone_number"],
                            "first_name": item["students__first_name"],
                            "student_id": item["students__id"],
                            "avatar": s3.get_link(item["students__profile__avatar"])
                            if item["students__profile__avatar"]
                            else s3.get_link("users/avatars/base_avatar.jpg"),
                            "last_name": item["students__last_name"],
                            "group_name": item["name"],
                            "school_name": school.name,
                            "mark_sum": item["mark_sum"],
                            "average_mark": item["average_mark"],
                            "date_added": item["date_added_student"],
                            "date_removed": item["date_removed_student"],
                            "is_deleted": True
                            if item["date_removed_student"] is not None
                            else False,
                            "progress": item["progress"],
                            "all_active_students": all_active_students,
                            "unique_students_count": unique_students_count,
                            "filtered_active_students": filtered_active_students,
                            "chat_uuid": UserChat.get_existed_chat_id_by_type(
                                chat_creator=user,
                                reciever=item["students__id"],
                                type="PERSONAL",
                            ),
                        }
                    )
                else:
                    serialized_data.append(
                        {
                            "course_id": item["course_id"],
                            "course_name": item["course_id__name"],
                            "group_id": item["group_id"],
                            "last_active": item["students__date_joined"],
                            "last_login": item["students__last_login"],
                            "email": item["students__email"],
                            "phone_number": item["students__phone_number"],
                            "first_name": item["students__first_name"],
                            "student_id": item["students__id"],
                            "avatar": s3.get_link(item["students__profile__avatar"])
                            if item["students__profile__avatar"]
                            else s3.get_link("users/avatars/base_avatar.jpg"),
                            "last_name": item["students__last_name"],
                            "group_name": item["name"],
                            "school_name": school.name,
                            "mark_sum": item["mark_sum"],
                            "average_mark": item["average_mark"],
                            "date_added": item["date_added_student"],
                            "date_removed": item["date_removed_student"],
                            "is_deleted": True
                            if item["date_removed_student"] is not None
                            else False,
                            "all_active_students": all_active_students,
                            "unique_students_count": unique_students_count,
                            "filtered_active_students": filtered_active_students,
                            "chat_uuid": UserChat.get_existed_chat_id_by_type(
                                chat_creator=user,
                                reciever=item["students__id"],
                                type="PERSONAL",
                            ),
                        }
                    )

            pagination_data = {
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serialized_data,
            }
            return Response(pagination_data)

        return Response(
            {"error": "Ошибка в запросе"}, status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True)
    def all_stats(self, request, pk, *args, **kwargs):
        queryset = StudentsGroup.objects.none()
        user = self.request.user
        school = self.get_object()
        if user.groups.filter(group__name="Teacher", school=school).exists():
            queryset = StudentsGroup.objects.filter(
                teacher_id=request.user, course_id__school=school
            )
        if user.groups.filter(group__name="Admin", school=school).exists():
            queryset = StudentsGroup.objects.filter(course_id__school=school)

        deleted_history_queryset = StudentsHistory.objects.none()

        hide_deleted = self.request.GET.get("hide_deleted")
        if not hide_deleted:
            deleted_history_queryset = StudentsHistory.objects.filter(
                students_group_id__course_id__school=school, is_deleted=True
            )

        # Поиск
        search_value = self.request.GET.get("search_value")
        if search_value:
            cleaned_phone = re.sub(r"\D", "", search_value)

            query = (
                Q(students__first_name__icontains=search_value)
                | Q(students__last_name__icontains=search_value)
                | Q(name__icontains=search_value)
                | Q(course_id__name__icontains=search_value)
            )

            if cleaned_phone:
                query |= Q(students__phone_number__icontains=cleaned_phone)

            # Регулярное выражение для проверки email
            email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"

            # Проверяем, является ли search_value email
            if re.match(email_regex, search_value):
                queryset = queryset.filter(Q(students__email__icontains=search_value))
            else:
                queryset = queryset.filter(query)

            deleted_history_query = (
                Q(user_id__first_name__icontains=search_value)
                | Q(user_id__last_name__icontains=search_value)
                | Q(user_id__email__icontains=search_value)
                | Q(students_group_id__name__icontains=search_value)
                | Q(students_group_id__course_id__name__icontains=search_value)
            )

            if cleaned_phone:
                deleted_history_query |= Q(
                    user_id__phone_number__icontains=cleaned_phone
                )

            # Регулярное выражение для проверки email
            email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"

            # Проверяем, является ли search_value email
            if re.match(email_regex, search_value):
                deleted_history_queryset = deleted_history_queryset.filter(
                    Q(user_id__email__icontains=search_value)
                )
            else:
                deleted_history_queryset = deleted_history_queryset.filter(
                    deleted_history_query
                )

        # Фильтры
        first_name = self.request.GET.get("first_name")
        if first_name:
            queryset = queryset.filter(students__first_name=first_name).distinct()
            deleted_history_queryset = deleted_history_queryset.filter(
                user__first_name=first_name
            ).distinct()
        last_name = self.request.GET.get("last_name")
        if last_name:
            queryset = queryset.filter(students__last_name=last_name).distinct()
            deleted_history_queryset = deleted_history_queryset.filter(
                user__last_name=last_name
            ).distinct()
        course_name = self.request.GET.get("course_name")
        if course_name:
            queryset = queryset.filter(course_id__name=course_name).distinct()
            deleted_history_queryset = deleted_history_queryset.filter(
                students_group_id__course_id__name=course_name
            ).distinct()
        group_name = self.request.GET.get("group_name")
        if group_name:
            queryset = queryset.filter(name=group_name).distinct()
            deleted_history_queryset = deleted_history_queryset.filter(
                students_group_id__name=group_name
            ).distinct()
        last_active_min = self.request.GET.get("last_active_min")
        if last_active_min:
            last_active_min = datetime.strptime(last_active_min, "%Y-%m-%d")
            queryset = queryset.filter(
                students__last_login__gte=last_active_min
            ).distinct()
            deleted_history_queryset = deleted_history_queryset.filter(
                user__last_login__gte=last_active_min
            ).distinct()
        last_active_max = self.request.GET.get("last_active_max")
        if last_active_max:
            last_active_max = datetime.strptime(last_active_max, "%Y-%m-%d")
            last_active_max += timedelta(days=1)
            queryset = queryset.filter(
                students__last_login__lte=last_active_max
            ).distinct()
            deleted_history_queryset = deleted_history_queryset.filter(
                user__last_login__lte=last_active_max
            ).distinct()
        last_active = self.request.GET.get("last_active")
        if last_active:
            last_active = datetime.strptime(last_active, "%Y-%m-%d")
            queryset = queryset.filter(students__last_login=last_active).distinct()
            deleted_history_queryset = deleted_history_queryset.filter(
                user__last_login=last_active
            ).distinct()
        mark_sum = self.request.GET.get("mark_sum")
        if mark_sum:
            queryset = queryset.annotate(mark_sum=Sum("students__user_homeworks__mark"))
            queryset = queryset.filter(mark_sum__exact=mark_sum)
            deleted_history_queryset = deleted_history_queryset.annotate(
                mark_sum=Sum("user__user_homeworks__mark")
            )
            deleted_history_queryset = deleted_history_queryset.filter(
                mark_sum__exact=mark_sum
            )

        average_mark = self.request.GET.get("average_mark")
        if average_mark:
            queryset = queryset.annotate(
                average_mark=Avg("students__user_homeworks__mark")
            )
            queryset = queryset.filter(average_mark__exact=average_mark)
            deleted_history_queryset = deleted_history_queryset.annotate(
                average_mark=Avg("students__user_homeworks__mark")
            )
            deleted_history_queryset = deleted_history_queryset.filter(
                average_mark__exact=average_mark
            )
        mark_sum_min = self.request.GET.get("mark_sum_min")
        if mark_sum_min:
            queryset = queryset.annotate(mark_sum=Sum("students__user_homeworks__mark"))
            queryset = queryset.filter(mark_sum__gte=mark_sum_min)
        mark_sum_max = self.request.GET.get("mark_sum_max")
        if mark_sum_max:
            queryset = queryset.annotate(mark_sum=Sum("students__user_homeworks__mark"))
            queryset = queryset.filter(mark_sum__lte=mark_sum_max)
        average_mark_min = self.request.GET.get("average_mark_min")
        if average_mark_min:
            queryset = queryset.annotate(
                average_mark=Avg("students__user_homeworks__mark")
            )
            queryset = queryset.filter(average_mark__gte=average_mark_min)
        average_mark_max = self.request.GET.get("average_mark_max")
        if average_mark_max:
            queryset = queryset.annotate(
                average_mark=Avg("students__user_homeworks__mark")
            )
            queryset = queryset.filter(average_mark__lte=average_mark_max)

        subquery_mark_sum = (
            UserHomework.objects.filter(user_id=OuterRef("students__id"))
            .values("user_id")
            .annotate(mark_sum=Sum("mark"))
            .values("mark_sum")
        )

        subquery_average_mark = (
            UserHomework.objects.filter(user_id=OuterRef("students__id"))
            .values("user_id")
            .annotate(avg=Avg("mark"))
            .values("avg")
        )

        subquery_date_added = (
            StudentsHistory.objects.filter(
                user_id=OuterRef("students__id"),
                students_group=OuterRef("group_id"),
                is_deleted=False,
            )
            .order_by("-date_added")
            .values("date_added")[:1]
        )

        subquery_date_removed = (
            StudentsHistory.objects.none()
            .order_by("-date_removed")
            .values("date_removed")[:1]
        )

        data = queryset.values(
            "course_id",
            "course_id__name",
            "group_id",
            "students__date_joined",
            "students__last_login",
            "students__email",
            "students__phone_number",
            "students__first_name",
            "students__id",
            "students__profile__avatar",
            "students__last_name",
            "name",
        ).annotate(
            mark_sum=Subquery(subquery_mark_sum),
            average_mark=Subquery(subquery_average_mark),
            date_added=Subquery(subquery_date_added),
            date_removed=Subquery(subquery_date_removed),
        )

        serialized_data = []
        for item in data:
            if not item["students__id"]:
                continue

            serialized_data.append(
                {
                    "course_id": item["course_id"],
                    "course_name": item["course_id__name"],
                    "group_id": item["group_id"],
                    "last_active": item["students__date_joined"],
                    "email": item["students__email"],
                    "phone_number": item["students__phone_number"],
                    "first_name": item["students__first_name"],
                    "student_id": item["students__id"],
                    "last_name": item["students__last_name"],
                    "group_name": item["name"],
                    "mark_sum": item["mark_sum"],
                    "average_mark": item["average_mark"],
                    "date_added": item["date_added"],
                    "date_removed": item["date_removed"],
                    "progress": progress_subquery(
                        item["students__id"], item["course_id"]
                    ),
                }
            )

        # Deleted students
        subquery_mark_sum_deleted = (
            UserHomework.objects.filter(user_id=OuterRef("user_id"))
            .values("user_id")
            .annotate(mark_sum=Sum("mark"))
            .values("mark_sum")
        )

        subquery_average_mark_deleted = (
            UserHomework.objects.filter(user_id=OuterRef("user_id"))
            .values("user_id")
            .annotate(avg=Avg("mark"))
            .values("avg")
        )

        data_deleted = deleted_history_queryset.values(
            "students_group_id__course_id",
            "students_group_id__course_id__name",
            "students_group_id",
            "user_id__date_joined",
            "user_id__email",
            "user_id__first_name",
            "user_id__phone_number",
            "user_id",
            "user_id__profile__avatar",
            "user_id__last_name",
            "students_group_id__name",
            "date_added",
            "date_removed",
        ).annotate(
            mark_sum=Subquery(subquery_mark_sum_deleted),
            average_mark=Subquery(subquery_average_mark_deleted),
        )

        for item in data_deleted:
            if not item["user_id"]:
                continue

            serialized_data.append(
                {
                    "course_id": item["students_group_id__course_id"],
                    "course_name": item["students_group_id__course_id__name"],
                    "group_id": item["students_group_id"],
                    "last_active": item["user_id__date_joined"],
                    "email": item["user_id__email"],
                    "phone_number": item["user_id__phone_number"],
                    "first_name": item["user_id__first_name"],
                    "student_id": item["user_id"],
                    "last_name": item["user_id__last_name"],
                    "group_name": item["students_group_id__name"],
                    "mark_sum": item["mark_sum"],
                    "average_mark": item["average_mark"],
                    "date_added": item["date_added"],
                    "date_removed": item["date_removed"],
                    "is_deleted": True,
                }
            )

        return Response(serialized_data)

    @action(detail=False, methods=["POST"])
    def create_documents(self, request, *args, **kwargs):

        all_schools = School.objects.all()
        for school in all_schools:
            if not SchoolDocuments.objects.filter(school=school).exists():
                SchoolDocuments.objects.create(school=school, user=school.owner)
        return Response("ok")


class TariffViewSet(WithHeadersViewSet, viewsets.ModelViewSet):
    """
    API endpoint для тарифов.
    """

    queryset = Tariff.objects.all()
    serializer_class = TariffSerializer
    http_method_names = ["get", "head"]


class AddPaymentMethodViewSet(viewsets.ModelViewSet):
    """
    API endpoint для добавления способа оплаты курсов
    """

    queryset = SchoolPaymentMethod.objects.all()
    serializer_class = SchoolPaymentMethodSerializer

    def get_payment_methods(self, school_id):
        payment_methods = SchoolPaymentMethod.objects.filter(school=school_id)
        serializer = self.get_serializer(payment_methods, many=True)
        return serializer.data

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            school_id = serializer.data["school"]
            response = self.get_payment_methods(school_id)
            return Response(response, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        school_id = request.query_params.get("school_id")
        if school_id:
            queryset = self.queryset.filter(school=school_id)
        else:
            queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["DELETE"])
    def delete(self, request):
        try:
            account_no = request.data.get("account_no")
            instance = self.queryset.get(account_no=account_no)
            instance.delete()
            school_id = instance.school_id
            response = self.get_payment_methods(school_id)
            return Response(response, status=status.HTTP_200_OK)
        except SchoolPaymentMethod.DoesNotExist:
            return Response(
                {"message": "Payment method not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProdamusPaymentLinkViewSet(viewsets.ModelViewSet):
    queryset = ProdamusPaymentLink.objects.all()
    serializer_class = ProdamusLinkSerializer

    def create(self, request):
        try:
            data = request.data
            signature_data = data.copy()
            signature_data.pop("school", None)
            signature_data.pop("api_key", None)
            signature_data.pop("payment_link", None)
            signature_data.pop("created", None)
            signature_data.pop("school_payment_method", None)

            signature = Hmac.create_signature(
                signature_data, request.data.get("api_key")
            )
            data["signature"] = signature
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            serializer.instance.signature = signature
            serializer.instance.save()
            created_id = serializer.instance.id

            return Response(
                {"id": created_id, "signature": signature},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            traceback_str = traceback.format_exc()
            return Response(
                {"error": str(e.args), "traceback": traceback_str},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def list(self, request):
        school_id = request.query_params.get("school_id")
        if school_id:
            queryset = self.queryset.filter(school_id=school_id)
        else:
            queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SchoolPaymentLinkViewSet(viewsets.ModelViewSet):
    """
    API endpoint для работы с ссылками оплаты курсов
    """

    queryset = SchoolExpressPayLink.objects.all()
    serializer_class = SchoolExpressPayLinkSerializer

    def create(self, request):
        data = request.data

        try:
            required_fields = [
                "invoice_no",
                "school_id",
                "payment_method",
                "payment_link",
                "amount",
                "api_key",
                "currency",
            ]
            for field in required_fields:
                if field not in data:
                    return Response(
                        {"error": f'Field "{field}" is required'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            payment_method_id = data["payment_method"]
            payment_method = SchoolPaymentMethod.objects.get(id=payment_method_id)

            SchoolExpressPayLink.objects.create(
                invoice_no=data["invoice_no"],
                school_id=data["school_id"],
                payment_method=payment_method,
                payment_link=data["payment_link"],
                amount=data["amount"],
                api_key=data["api_key"],
                currency=data["currency"],
            )
            return Response({"response": "success"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        school_id = request.query_params.get("school_id")
        if school_id:
            queryset = self.queryset.filter(school_id=school_id)
        else:
            queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["DELETE"])
    def delete(self, request):
        try:
            invoice_no = request.data.get("invoice_no")
            instance = self.queryset.get(invoice_no=invoice_no)
            instance.delete()
            return Response(
                {"message": "Payment link deleted"}, status=status.HTTP_200_OK
            )
        except SchoolExpressPayLink.DoesNotExist:
            return Response(
                {"message": "Payment link not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def partial_update(self, request, pk=None):
        try:
            data = request.data
            payment_link = data["data"].get("payment_link")
            new_payment_link_data = {
                "status": data["data"].get("status"),
                "first_name": data["data"].get("first_name"),
                "last_name": data["data"].get("last_name"),
                "patronymic": data["data"].get("patronymic"),
            }

            instance = self.queryset.get(payment_link=payment_link)
            for key, value in new_payment_link_data.items():
                setattr(instance, key, value)
            instance.save()

            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SchoolExpressPayLink.DoesNotExist:
            return Response(
                {"message": "Payment link not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SchoolStudentsTableSettingsViewSet(viewsets.ViewSet):
    """
    Управление группировкой учеников в таблицах
    """

    queryset = SchoolStudentsTableSettings.objects.all()
    serializer_class = SchoolStudentsTableSettingsSerializer
    lookup_field = "school_id"

    def retrieve(self, request, *args, **kwargs):
        school_id = kwargs.get("school_id")
        instance = self.get_object(school_id)
        serializer = self.serializer_class(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        school_id = request.data.get("school")
        instance = self.get_object(school_id)
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def get_object(self, school_id):
        obj, created = SchoolStudentsTableSettings.objects.get_or_create(
            school_id=school_id
        )
        return obj


class SchoolTasksViewSet(WithHeadersViewSet, SchoolMixin, APIView):
    """
    API endpoint для работы с заданиями для школы
    """

    queryset = SchoolTask.objects.all()
    serializer_class = SchoolTaskSummarySerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        tags=["school_tasks"],
        operation_description="Получение заданий для школы",
        operation_summary="Получение заданий для школы",
    )
    def get(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)

        total_tasks = self.queryset.filter(school=school).count()
        total_completed_tasks = self.queryset.filter(
            school=school, completed=True
        ).count()
        completion_percentage = (
            (total_completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        )

        data = {
            "total_tasks": total_tasks,
            "total_completed_tasks": total_completed_tasks,
            "completion_percentage": round(completion_percentage),
            "tasks": [
                {"task": task.get_task_display(), "completed": task.completed}
                for task in self.queryset.filter(school=school)
            ],
        }

        serializer = SchoolTaskSummarySerializer(data)
        return Response(serializer.data)
