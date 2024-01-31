from datetime import datetime, timedelta

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from courses.models import (
    Homework,
    Lesson,
    Section,
    SectionTest,
    StudentsGroup,
    UserHomework,
)
from courses.models.students.students_history import StudentsHistory
from courses.paginators import StudentsPagination
from courses.services import get_student_progress
from django.db.models import Avg, OuterRef, Subquery, Sum, Count, Q
from django.http import HttpResponse
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from schools.models import School, SchoolHeader, Tariff, TariffPlan
from schools.serializers import (
    SchoolGetSerializer,
    SchoolSerializer,
    SchoolUpdateSerializer,
    SelectTrialSerializer,
    TariffSerializer,
)
from users.models import Profile, UserGroup, UserRole
from users.serializers import UserProfileGetSerializer
from chats.models import UserChat, Chat
import pytz

s3 = UploadToS3()


class SchoolViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    """Эндпоинт на получение, создания, изменения и удаления школ \n
    <h2>/api/{school_name}/schools/</h2>\n
    Разрешения для просмотра школ (любой пользователь)\n
    Разрешения для создания и изменения школы (только пользователи зарегистрированные указавшие email и phone_number')"""

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser,)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return SchoolGetSerializer
        if self.action in ["select_trial"]:
            return SelectTrialSerializer
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
            self.action in ["stats"]
            and user.groups.filter(group__name__in=["Teacher", "Admin"]).exists()
        ):
            return permissions
        if self.action in ["list", "retrieve", "create"]:
            # Разрешения для просмотра домашних заданий (любой пользователь школы)
            if user.groups.filter(group__name__in=["Teacher", "Student"]).exists():
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
        if not request.user.email or not request.user.phone_number:
            raise PermissionDenied("Email и phone number пользователя обязательны.")
        # Проверка количества школ, которыми владеет пользователь
        if School.objects.filter(owner=request.user).count() >= 2:
            raise PermissionDenied(
                "Пользователь может быть владельцем только двух школ."
            )

        serializer = SchoolSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if School.objects.filter(name=serializer.validated_data["name"]).exists():
            return HttpResponse("Название школы уже существует.", status=400)

        school = serializer.save(
            owner=request.user,
            tariff=Tariff.objects.get(name=TariffPlan.INTERN.value),
        )
        if school:
            SchoolHeader.objects.create(school=school, name=school.name)
        # Создание записи в модели UserGroup для добавления пользователя в качестве администратора
        group_admin = UserRole.objects.get(name="Admin")
        user_group = UserGroup(user=request.user, group=group_admin, school=school)
        user_group.save()

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

    @action(detail=True, methods=["post"])
    def select_trial(self, request, pk=None):
        school = self.get_object()

        # Проверка разрешений для выбора пробного тарифа
        if school.owner != request.user:
            return Response(
                {
                    "error": "У вас нет прав на установку пробного периода для этой школы"
                },
                status=403,
            )

        # Проверка, что пробный тариф еще не использован
        if not school.used_trial:
            serializer = SelectTrialSerializer(school, data=request.data)
            serializer.is_valid(raise_exception=True)
            tariff_choice = serializer.validated_data["tariff"]

            # Получение объекта Tariff по выбранному тарифу
            try:
                tariff = Tariff.objects.get(name=tariff_choice)
            except Tariff.DoesNotExist:
                return Response({"error": "Указан некорректный тариф"}, status=400)
            # Установка выбранного тарифа для школы
            school.tariff = tariff
            school.used_trial = True
            school.trial_end_date = timezone.now() + timezone.timedelta(days=14)
            school.save()

            return Response(
                {"message": "Пробный период успешно установлен"}, status=200
            )
        else:
            return Response({"error": "Пробный период уже был использован"}, status=400)

    def get_student_sections_and_availability(self, student_id):
        student_groups = StudentsGroup.objects.filter(students__id=student_id)
        student_data = []

        for group in student_groups:
            group_data = {"group_id": group.group_id, "sections": []}

            course = group.course_id
            sections = Section.objects.filter(course=course)

            for section in sections:
                lessons_data = []
                for lesson in section.lessons.all():
                    availability = lesson.is_available_for_student(student_id)
                    if availability is None:
                        availability = True
                    try:
                        Homework.objects.get(baselesson_ptr=lesson.id)
                        obj_type = "homework"
                    except Homework.DoesNotExist:
                        pass
                    try:
                        Lesson.objects.get(baselesson_ptr=lesson.id)
                        obj_type = "lesson"
                    except Lesson.DoesNotExist:
                        pass
                    try:
                        SectionTest.objects.get(baselesson_ptr=lesson.id)
                        obj_type = "test"
                    except SectionTest.DoesNotExist:
                        pass

                    lesson_data = {
                        "lesson_id": lesson.id,
                        "type": obj_type,
                        "name": lesson.name,
                        "availability": availability,
                        "active": lesson.active,
                    }
                    lessons_data.append(lesson_data)

                section_data = {
                    "section_id": section.section_id,
                    "name": section.name,
                    "lessons": lessons_data,
                }
                group_data["sections"].append(section_data)

            student_data.append(group_data)

        return student_data

    @action(detail=True, methods=["get"])
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "student_id",
                openapi.IN_QUERY,
                description="ID студента",
                type=openapi.TYPE_INTEGER,
            ),
        ],
    )
    def section_student(self, request, pk=None, *args, **kwargs):
        school = self.get_object()
        student_id = request.query_params.get("student_id", None)
        if not student_id:
            return Response(
                {"error": "Не указан ID студента"}, status=status.HTTP_400_BAD_REQUEST
            )
        student_data = self.get_student_sections_and_availability(student_id)
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
            queryset = queryset.filter(
                Q(students__first_name__icontains=search_value) |
                Q(students__last_name__icontains=search_value) |
                Q(students__email__icontains=search_value) |
                Q(name__icontains=search_value) |
                Q(course_id__name__icontains=search_value)
            )
            deleted_history_queryset = deleted_history_queryset.filter(
                Q(user_id__first_name__icontains=search_value) |
                Q(user_id__last_name__icontains=search_value) |
                Q(user_id__email__icontains=search_value) |
                Q(students_group_id__name__icontains=search_value) |
                Q(students_group_id__course_id__name__icontains=search_value)
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
            last_active_min = datetime.strptime(last_active_min, '%Y-%m-%d')
            last_active_min -= timedelta(days=1)
            queryset = queryset.filter(
                students__last_login__gte=last_active_min
            ).distinct()
            deleted_history_queryset = deleted_history_queryset.filter(
                user__last_login__gte=last_active_min
            ).distinct()
        last_active_max = self.request.GET.get("last_active_max")
        if last_active_max:
            last_active_max = datetime.strptime(last_active_max, '%Y-%m-%d')
            last_active_max += timedelta(days=1)
            queryset = queryset.filter(
                students__last_login__lte=last_active_max
            ).distinct()
            deleted_history_queryset = deleted_history_queryset.filter(
                user__last_login__lte=last_active_max
            ).distinct()
        last_active = self.request.GET.get("last_active")
        if last_active:
            last_active = datetime.strptime(last_active, '%Y-%m-%d')
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
            .values("date_added")
        )

        subquery_date_removed = (
            StudentsHistory.objects.none()
            .order_by("-date_removed")
            .values("date_removed")
        )

        data = queryset.values(
            "course_id",
            "course_id__name",
            "group_id",
            "students__date_joined",
            "students__last_login",
            "students__email",
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

        filtered_active_students = data.count()

        serialized_data = []
        for item in data:
            if not item["students__id"]:
                continue
            profile = Profile.objects.filter(user_id=item["students__id"]).first()
            if profile is not None:
                serializer = UserProfileGetSerializer(
                    profile, context={"request": self.request}
                )

            serialized_data.append(
                {
                    "course_id": item["course_id"],
                    "course_name": item["course_id__name"],
                    "group_id": item["group_id"],
                    "last_active": item["students__date_joined"],
                    "last_login": item["students__last_login"],
                    "email": item["students__email"],
                    "first_name": item["students__first_name"],
                    "student_id": item["students__id"],
                    "avatar": serializer.data["avatar"],
                    "last_name": item["students__last_name"],
                    "group_name": item["name"],
                    "school_name": school.name,
                    "mark_sum": item["mark_sum"],
                    "average_mark": item["average_mark"],
                    "date_added": item["date_added"],
                    "date_removed": item["date_removed"],
                    "is_deleted": False,
                    "progress": get_student_progress(
                        item["students__id"],
                        item["course_id"],
                        item["group_id"],
                    ),
                    "all_active_students": all_active_students,
                    "filtered_active_students": filtered_active_students,
                    "chat_uuid": UserChat.get_existed_chat_id_by_type(
                        chat_creator=user,
                        reciever=item["students__id"],
                        type="PERSONAL"),
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
            profile = Profile.objects.filter(user_id=item["user_id"]).first()
            if profile is not None:
                serializer = UserProfileGetSerializer(
                    profile, context={"request": self.request}
                )
            serialized_data.append(
                {
                    "course_id": item["students_group_id__course_id"],
                    "course_name": item["students_group_id__course_id__name"],
                    "group_id": item["students_group_id"],
                    "last_active": item["user_id__date_joined"],
                    "email": item["user_id__email"],
                    "first_name": item["user_id__first_name"],
                    "student_id": item["user_id"],
                    "avatar": serializer.data["avatar"],
                    "last_name": item["user_id__last_name"],
                    "group_name": item["students_group_id__name"],
                    "school_name": school.name,
                    "mark_sum": item["mark_sum"],
                    "average_mark": item["average_mark"],
                    "date_added": item["date_added"],
                    "date_removed": item["date_removed"],
                    "is_deleted": True,
                }
            )

        # Сортировка
        sort_by = request.GET.get("sort_by", "date_added")
        sort_order = request.GET.get("sort_order", "desc")
        default_date = datetime(2023, 11, 1, tzinfo=pytz.UTC)
        if sort_by in [
            'first_name',
            'last_name',
            'email',
            'group_name',
            'course_name',
            'date_added',
            'date_removed',
            'progress',
            'average_mark',
            'mark_sum',
            'last_active',
        ]:
            if sort_order == "asc":
                if sort_by in ['date_added', 'date_removed', 'last_active']:
                    sorted_data = sorted(
                        serialized_data,
                        key=lambda x: x.get(sort_by, datetime.min)
                        if x.get(sort_by) is not None else default_date)
                elif sort_by in ['progress', 'average_mark', 'mark_sum',]:
                    sorted_data = sorted(
                        serialized_data,
                        key=lambda x: x.get(sort_by, 0)
                        if x.get(sort_by) is not None else 0)
                else:
                    sorted_data = sorted(serialized_data, key=lambda x: str(x.get(sort_by, '') or '').lower())

            else:
                if sort_by in ['date_added', 'date_removed', 'last_active']:
                    sorted_data = sorted(
                        serialized_data,
                        key=lambda x: x.get(sort_by, datetime.min)
                        if x.get(sort_by) is not None else default_date, reverse=True)
                elif sort_by in ['progress', 'average_mark', 'mark_sum',]:
                    sorted_data = sorted(
                        serialized_data,
                        key=lambda x: x.get(sort_by, 0)
                        if x.get(sort_by) is not None else 0, reverse=True)
                else:
                    sorted_data = sorted(
                        serialized_data,
                        key=lambda x: str(x.get(sort_by, '') or '').lower(), reverse=True)

            paginator = StudentsPagination()
            paginated_data = paginator.paginate_queryset(sorted_data, request)
            return paginator.get_paginated_response(paginated_data)

        return Response({"error": "Ошибка в запросе"}, status=status.HTTP_400_BAD_REQUEST)


class TariffViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    """
    API endpoint для тарифов.

    """

    queryset = Tariff.objects.all()
    serializer_class = TariffSerializer
    http_method_names = ["get", "head"]

