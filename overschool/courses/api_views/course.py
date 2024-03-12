from datetime import datetime, timedelta

import pytz
from chats.models import Chat, UserChat
from common_services.apply_swagger_auto_schema import apply_swagger_auto_schema
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from courses.api_views.students_group import get_student_training_duration
from courses.models import (
    Course,
    Homework,
    Lesson,
    SectionTest,
    StudentsGroup,
    TrainingDuration,
    UserProgressLogs,
)
from courses.models.courses.section import Section
from courses.models.homework.user_homework import UserHomework
from courses.models.students.students_history import StudentsHistory
from courses.paginators import StudentsPagination, UserHomeworkPagination
from courses.serializers import (
    CourseGetSerializer,
    CourseSerializer,
    CourseWithGroupsSerializer,
    SectionSerializer,
    StudentsGroupSerializer,
)
from courses.services import get_student_progress
from django.db.models import (
    Avg,
    Case,
    Count,
    Exists,
    F,
    IntegerField,
    Max,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.functions import ExtractDay, Now
from django.db.models.lookups import GreaterThan, LessThan
from django.forms.models import model_to_dict
from django.utils import timezone
from django.utils.decorators import method_decorator
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from schools.models import School, TariffPlan
from schools.school_mixin import SchoolMixin
from users.models import Profile
from users.serializers import UserProfileGetSerializer

from .schemas.course import CoursesSchemas

s3 = UploadToS3()


@method_decorator(
    name="update",
    decorator=CoursesSchemas.courses_update_schema(),
)
@method_decorator(
    name="partial_update",
    decorator=CoursesSchemas.courses_update_schema(),
)
class CourseViewSet(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet
):
    """Эндпоинт для просмотра, создания, изменения и удаления курсов \n
    <h2>/api/{school_name}/courses/</h2>\n
    Получать курсы может любой пользователь. \n
    Создавать, изменять, удалять - пользователь с правами группы Admin."""

    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = UserHomeworkPagination
    parser_classes = (MultiPartParser,)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return CourseGetSerializer
        elif self.action == "with_student_groups":
            return CourseWithGroupsSerializer
        else:
            return CourseSerializer

    def get_permissions(self, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return permissions
        if self.action in [
            "list",
            "retrieve",
            "sections",
            "get_students_for_course",
            "user_count_by_month",
            "student_groups",
        ]:
            # Разрешения для просмотра курсов (любой пользователь школы)
            if user.groups.filter(
                group__name__in=["Student", "Teacher"], school=school_id
            ).exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_queryset(self, *args, **kwargs):
        if getattr(self, "swagger_fake_view", False):
            return (
                Course.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        user = self.request.user
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return Course.objects.filter(school__name=school_name)

        if user.groups.filter(group__name="Student", school=school_id).exists():
            sub_history = StudentsHistory.objects.filter(
                students_group=OuterRef("group_id"), user=user, is_deleted=False
            ).values("date_added")[:1]
            sub_duration = TrainingDuration.objects.filter(
                students_group=OuterRef("group_id"), user=user
            ).values("limit")[:1]
            student_groups = StudentsGroup.objects.filter(
                course_id__school__name=school_name, students=user
            )
            course_ids = student_groups.values_list("course_id", flat=True)
            # Добавляем информацию для учеников о продолжительности их обучения
            sub_group = student_groups.filter(course_id=OuterRef("course_id")).annotate(
                limit=Case(
                    When(Exists(Subquery(sub_duration)), then=Subquery(sub_duration)),
                    When(training_duration__gt=0, then=F("training_duration")),
                    default=None,
                    output_field=IntegerField(),
                ),
                past_period=ExtractDay(Now() - Subquery(sub_history)),
                remaining_period=Case(
                    When(
                        GreaterThan(F("limit"), 0)
                        & GreaterThan(F("limit"), F("past_period")),
                        then=F("limit") - F("past_period"),
                    ),
                    When(limit__gt=0, then=0),
                    default=None,
                ),
            )
            courses = Course.objects.filter(course_id__in=course_ids).annotate(
                limit=Subquery(sub_group.values("limit")[:1]),
                remaining_period=Subquery(sub_group.values("remaining_period")[:1]),
            )
            return courses

        if user.groups.filter(group__name="Teacher", school=school_id).exists():
            course_ids = StudentsGroup.objects.filter(
                course_id__school__name=school_name, teacher_id=user.pk
            ).values_list("course_id", flat=True)
            return Course.objects.filter(course_id__in=course_ids)

        return Course.objects.none()

    def create(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_obj = School.objects.get(name=school_name)
        school_id = school_obj.school_id
        school = self.request.data.get("school")

        if int(school) != school_id:
            return Response(
                "Указанный id школы не соответствует id текущей школы.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            school_obj.tariff.name
            in [TariffPlan.INTERN, TariffPlan.JUNIOR, TariffPlan.MIDDLE]
            and school_obj.course_school.count() >= school_obj.tariff.number_of_courses
        ):
            return Response(
                "Превышено количество курсов для выбранного тарифа",
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CourseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course = serializer.save(photo=None)

        if request.FILES.get("photo"):
            photo = s3.upload_course_image(request.FILES["photo"], course)
            course.photo = photo
            course.save()
            serializer = CourseGetSerializer(course)

        # Чат с типом "COURSE" и именем, связанным с курсом
        # chat_name = f"Чат курса '{course.name}'"
        # chat = Chat.objects.create(name=chat_name, type="COURSE")
        #
        # admin = request.user
        #
        # UserChat.objects.create(user=admin, chat=chat)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
        school = self.request.data.get("school")
        if school and int(school) != school_id:
            return Response(
                "Указанный id школы не соответствует id текущей школы.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance = self.get_object()
        serializer = CourseSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if request.FILES.get("photo"):
            if instance.photo:
                s3.delete_file(str(instance.photo))
            serializer.validated_data["photo"] = s3.upload_course_image(
                request.FILES["photo"], instance
            )
        else:
            serializer.validated_data["photo"] = instance.photo

        self.perform_update(serializer)
        course = Course.objects.filter(pk=instance.course_id).first()
        serializer = CourseGetSerializer(course)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        school_id = instance.school.school_id

        # Получаем список файлов, хранящихся в папке удаляемого курса
        files_to_delete = s3.get_list_objects(
            "{}_school/{}_course".format(school_id, instance.pk)
        )
        # Удаляем все файлы и сегменты, связанные с удаляемым курсом
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

    @action(detail=True, methods=["GET"])
    def get_students_for_course(self, request, pk=None, *args, **kwargs):
        """Все студенты одного курса\n
        <h2>/api/{school_name}/courses/{course_id}/get_students_for_course/</h2>\n"""

        queryset = StudentsGroup.objects.none()
        user = self.request.user
        course = self.get_object()
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)
        if user.groups.filter(group__name="Teacher", school=school).exists():
            queryset = StudentsGroup.objects.filter(
                teacher_id=request.user, course_id=course.course_id
            )
        if user.groups.filter(group__name="Admin", school=school).exists():
            queryset = StudentsGroup.objects.filter(course_id=course.course_id)

        all_active_students = queryset.count()

        # Поиск
        search_value = self.request.GET.get("search_value")
        if search_value:
            queryset = queryset.filter(
                Q(students__first_name__icontains=search_value)
                | Q(students__last_name__icontains=search_value)
                | Q(students__email__icontains=search_value)
                | Q(name__icontains=search_value)
            )

        # Фильтры
        first_name = self.request.GET.get("first_name")
        if first_name:
            queryset = queryset.filter(students__first_name=first_name).distinct()
        last_name = self.request.GET.get("last_name")
        if last_name:
            queryset = queryset.filter(students__last_name=last_name).distinct()
        group_name = self.request.GET.get("group_name")
        if group_name:
            queryset = queryset.filter(name=group_name).distinct()
        last_active_min = self.request.GET.get("last_active_min")
        if last_active_min:
            last_active_min = datetime.strptime(last_active_min, "%Y-%m-%d")
            queryset = queryset.filter(
                students__last_login__gte=last_active_min
            ).distinct()
        last_active_max = self.request.GET.get("last_active_max")
        if last_active_max:
            last_active_max = datetime.strptime(last_active_max, "%Y-%m-%d")
            last_active_max += timedelta(days=1)
            queryset = queryset.filter(
                students__last_login__lte=last_active_max
            ).distinct()
        last_active = self.request.GET.get("last_active")
        if last_active:
            queryset = queryset.filter(students__last_login=last_active).distinct()
        mark_sum = self.request.GET.get("mark_sum")
        if mark_sum:
            queryset = queryset.annotate(mark_sum=Sum("students__user_homeworks__mark"))
            queryset = queryset.filter(mark_sum__exact=mark_sum)
        average_mark = self.request.GET.get("average_mark")
        if average_mark:
            queryset = queryset.annotate(
                average_mark=Avg("students__user_homeworks__mark")
            )
            queryset = queryset.filter(average_mark__exact=average_mark)
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
        filtered_active_students = queryset.count()
        serialized_data = []
        for item in data:
            if not item["students__id"]:
                continue
            profile = Profile.objects.get(user_id=item["students__id"])
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
                        type="PERSONAL",
                    ),
                }
            )

        # Сортировка
        sort_by = request.GET.get("sort_by", "date_added")
        sort_order = request.GET.get("sort_order", "desc")
        default_date = datetime(2023, 11, 1, tzinfo=pytz.UTC)
        if sort_by in [
            "first_name",
            "last_name",
            "email",
            "group_name",
            "course_name",
            "date_added",
            "date_removed",
            "progress",
            "average_mark",
            "mark_sum",
            "last_active",
        ]:
            if sort_order == "asc":
                if sort_by in [
                    "date_added",
                    "date_removed",
                    "last_active",
                ]:
                    sorted_data = sorted(
                        serialized_data,
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
                        serialized_data,
                        key=lambda x: x.get(sort_by, 0)
                        if x.get(sort_by) is not None
                        else 0,
                    )
                else:
                    sorted_data = sorted(
                        serialized_data,
                        key=lambda x: str(x.get(sort_by, "") or "").lower(),
                    )

            else:
                if sort_by in [
                    "date_added",
                    "date_removed",
                    "last_active",
                ]:
                    sorted_data = sorted(
                        serialized_data,
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
                        serialized_data,
                        key=lambda x: x.get(sort_by, 0)
                        if x.get(sort_by) is not None
                        else 0,
                        reverse=True,
                    )
                else:
                    sorted_data = sorted(
                        serialized_data,
                        key=lambda x: str(x.get(sort_by, "") or "").lower(),
                        reverse=True,
                    )

            paginator = StudentsPagination()
            paginated_data = paginator.paginate_queryset(sorted_data, request)
            return paginator.get_paginated_response(paginated_data)

        return Response(
            {"error": "Ошибка в запросе"}, status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=["GET"])
    def get_all_students_for_course(self, request, pk=None, *args, **kwargs):
        """Все студенты одного курса без пагинации\n
        <h2>/api/{school_name}/courses/{course_id}/get_students_for_course/</h2>\n"""

        queryset = StudentsGroup.objects.none()
        user = self.request.user
        course = self.get_object()
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)
        if user.groups.filter(group__name="Teacher", school=school).exists():
            queryset = StudentsGroup.objects.filter(
                teacher_id=request.user, course_id=course.course_id
            )
        if user.groups.filter(group__name="Admin", school=school).exists():
            queryset = StudentsGroup.objects.filter(course_id=course.course_id)

        # Поиск
        search_value = self.request.GET.get("search_value")
        if search_value:
            queryset = queryset.filter(
                Q(students__first_name__icontains=search_value)
                | Q(students__last_name__icontains=search_value)
                | Q(students__email__icontains=search_value)
                | Q(name__icontains=search_value)
            )

        # Фильтры
        first_name = self.request.GET.get("first_name")
        if first_name:
            queryset = queryset.filter(students__first_name=first_name).distinct()
        last_name = self.request.GET.get("last_name")
        if last_name:
            queryset = queryset.filter(students__last_name=last_name).distinct()
        group_name = self.request.GET.get("group_name")
        if group_name:
            queryset = queryset.filter(name=group_name).distinct()
        last_active_min = self.request.GET.get("last_active_min")
        if last_active_min:
            last_active_min = datetime.strptime(last_active_min, "%Y-%m-%d")
            queryset = queryset.filter(
                students__last_login__gte=last_active_min
            ).distinct()
        last_active_max = self.request.GET.get("last_active_max")
        if last_active_max:
            last_active_max = datetime.strptime(last_active_max, "%Y-%m-%d")
            last_active_max += timedelta(days=1)
            queryset = queryset.filter(
                students__last_login__lte=last_active_max
            ).distinct()
        last_active = self.request.GET.get("last_active")
        if last_active:
            queryset = queryset.filter(students__last_login=last_active).distinct()
        mark_sum = self.request.GET.get("mark_sum")
        if mark_sum:
            queryset = queryset.annotate(mark_sum=Sum("students__user_homeworks__mark"))
            queryset = queryset.filter(mark_sum__exact=mark_sum)
        average_mark = self.request.GET.get("average_mark")
        if average_mark:
            queryset = queryset.annotate(
                average_mark=Avg("students__user_homeworks__mark")
            )
            queryset = queryset.filter(average_mark__exact=average_mark)
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
            courses = Course.objects.filter(course_id=item["course_id"])
            serialized_data.append(
                {
                    "student_id": item["students__id"],
                    "first_name": item["students__first_name"],
                    "last_name": item["students__last_name"],
                    "email": item["students__email"],
                    "course_name": item["course_id__name"],
                    "group_name": item["name"],
                    "last_active": item["students__date_joined"],
                    "mark_sum": item["mark_sum"],
                    "average_mark": item["average_mark"],
                    "date_added": item["date_added"],
                    "date_removed": item["date_removed"],
                    "progress": get_student_progress(
                        item["students__id"],
                        item["course_id"],
                        item["group_id"],
                    ),
                }
            )

        return Response(serialized_data)

    @action(detail=True)
    def clone(self, request, pk, *args, **kwargs):
        """Клонирование курса\n
        <h2>/api/{school_name}/courses/{course_id}/clone/</h2>\n
        Клонирование курса"""

        course = self.get_object()
        max_order = Course.objects.all().aggregate(Max("order"))["order__max"]
        course_copy = course.make_clone(
            attrs={"name": f"{course.name}-копия", "order": max_order + 1}
        )
        queryset = Course.objects.filter(pk=course_copy.pk)
        return Response(queryset.values())

    @action(detail=True)
    def sections(self, request, pk, *args, **kwargs):
        """Данные по всем секциям курс\n
        <h2>/api/{school_name}/courses/{course_id}/sections/</h2>\n
        Данные по всем секциям курса"""

        course = self.get_object()
        queryset = Course.objects.filter(course_id=course.pk)

        user = self.request.user
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)

        group = None
        if user.groups.filter(group__name="Student", school=school).exists():
            try:
                group = StudentsGroup.objects.get(students=user, course_id_id=course.pk)
                limit = get_student_training_duration(group, user.id)
                if limit:
                    history = StudentsHistory.objects.get(
                        user=user,
                        students_group=group,
                        is_deleted=False,
                    )
                    if history.date_added + timedelta(days=limit) < timezone.now():
                        return Response(
                            {"error": "Срок доступа к курсу истек."},
                            status=status.HTTP_403_FORBIDDEN,
                        )
            except Exception:
                raise NotFound("Ошибка поиска группы пользователя 1.")

        elif user.groups.filter(group__name="Teacher", school=school).exists():
            try:
                group = StudentsGroup.objects.get(
                    teacher_id=user.pk, course_id_id=course.pk
                )
            except Exception:
                raise NotFound("Ошибка поиска группы пользователя.")

        data = queryset.values(
            course=F("course_id"),
            course_name=F("name"),
            section_name=F("sections__name"),
            section=F("sections__section_id"),
            section_order=F("sections__order"),
        ).order_by("sections__order")
        result_data = dict(
            course_name=data[0]["course_name"],
            course_id=data[0]["course"],
        )

        if group:
            result_data["group_settings"] = {
                "task_submission_lock": group.group_settings.task_submission_lock,
                "strict_task_order": group.group_settings.strict_task_order,
            }
            result_data["teacher_id"] = group.teacher_id_id

        result_data["sections"] = []

        lesson_progress = UserProgressLogs.objects.filter(user_id=user.pk)
        types = {0: "homework", 1: "lesson", 2: "test"}
        for index, value in enumerate(data):
            result_data["sections"].append(
                {
                    "section_name": value["section_name"],
                    "section": value["section"],
                    "lessons": [],
                }
            )
            if user.groups.filter(group__name="Admin", school=school).exists():
                a = Homework.objects.filter(section=value["section"])
                b = Lesson.objects.filter(section=value["section"])
                c = SectionTest.objects.filter(section=value["section"])
            elif user.groups.filter(
                group__name__in=[
                    "Student",
                    "Teacher",
                ],
                school=school,
            ).exists():
                a = Homework.objects.filter(section=value["section"], active=True)
                b = Lesson.objects.filter(section=value["section"], active=True)
                c = SectionTest.objects.filter(section=value["section"], active=True)
                if user.groups.filter(group__name="Student", school=school).exists():
                    a = a.exclude(lessonavailability__student=user)
                    b = b.exclude(lessonavailability__student=user)
                    c = c.exclude(lessonavailability__student=user)

            for i in enumerate((a, b, c)):
                for obj in i[1]:
                    dict_obj = model_to_dict(obj)
                    result_data["sections"][index]["lessons"].append(
                        {
                            "type": types[i[0]],
                            "order": dict_obj["order"],
                            "name": dict_obj["name"],
                            "id": obj.pk,
                            "baselesson_ptr_id": obj.baselesson_ptr_id,
                            "section_id": obj.section_id,
                            "active": obj.active,
                            "viewed": lesson_progress.filter(
                                lesson_id=obj.baselesson_ptr_id, viewed=True
                            ).exists(),
                            "completed": lesson_progress.filter(
                                lesson_id=obj.baselesson_ptr_id, completed=True
                            ).exists(),
                        }
                    )
            result_data["sections"][index]["lessons"].sort(
                key=lambda x: x["order"] if x["order"] is not None else 0
            )
        return Response(result_data)

    @action(detail=True)
    def user_count_by_month(self, request, pk, *args, **kwargs):
        """Кол-во новых пользователей курса за месяц\n
        <h2>/api/{school_name}/courses/{course_id}/user_count_by_month/</h2>\n
        Кол-во новых пользователей курса за месяц, по дефолту стоит текущий месяц,
        для конкретного месяца указываем параметр month_number=""
        """
        queryset = StudentsGroup.objects.none()
        user = self.request.user
        course = self.get_object()
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)
        if user.groups.filter(
            group__name__in=["Admin", "Teacher"], school=school
        ).exists():
            queryset = StudentsGroup.objects.filter(course_id=course.course_id)

        month_number = request.GET.get("month_number", datetime.now().month)
        queryset = queryset.filter(students__date_joined__month=month_number)

        datas = queryset.values(course=F("course_id")).annotate(
            students_sum=Count("students__id")
        )

        for data in datas:
            data["graphic_data"] = queryset.values(
                course=F("course_id"), date=F("students__date_joined__day")
            ).annotate(students_sum=Count("students__id"))

        page = self.paginate_queryset(datas)
        if page is not None:
            return self.get_paginated_response(page)
        return Response(datas)

    @action(detail=True)
    def student_groups(self, request, pk, *args, **kwargs):
        """Список всех групп курса\n
        <h2>/api/{school_name}/courses/{course_id}/students_groups/</h2>\n
        Список всех групп курса"""

        queryset = StudentsGroup.objects.none()
        user = self.request.user
        course = self.get_object()
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)
        if user.groups.filter(group__name="Teacher", school=school).exists():
            queryset = StudentsGroup.objects.filter(
                teacher_id=request.user, course_id=course.course_id
            )
        if user.groups.filter(group__name="Admin", school=school).exists():
            queryset = StudentsGroup.objects.filter(course_id=course.course_id)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = StudentsGroupSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = StudentsGroupSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["GET"])
    def with_student_groups(self, request, *args, **kwargs):
        """Список курсов вместе с группами\n
        <h2>/api/{school_name}/courses/with_student_groups/</h2>\n
        Список курсов вместе с группами"""

        # Отбираем курсы, в которых есть студенческие группы
        queryset = (
            self.get_queryset()
            .annotate(groups_count=Count("group_course_fk__group_id"))
            .exclude(groups_count=0)
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


CourseViewSet = apply_swagger_auto_schema(
    tags=["courses"], excluded_methods=["partial_update", "update"]
)(CourseViewSet)
