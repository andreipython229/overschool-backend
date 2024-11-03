import re
from datetime import datetime, timedelta

import pytz
from chats.models import Chat, UserChat
from common_services.apply_swagger_auto_schema import apply_swagger_auto_schema
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from courses.api_views.students_group import get_student_training_duration
from courses.models import (
    BaseLessonBlock,
    Course,
    CourseCopy,
    Folder,
    Homework,
    Lesson,
    SectionTest,
    StudentsGroup,
    TrainingDuration,
    UserProgressLogs,
    UserTest,
)
from courses.models.courses.course import Public
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
from courses.services import get_student_progress, progress_subquery
from django.db import transaction
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
from users.models import Profile, User

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
            if (
                user.groups.filter(
                    group__name__in=["Student", "Teacher"], school=school_id
                ).exists()
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
                Course.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        user = self.request.user
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        if user.groups.filter(group__name="Admin", school=school_id).exists():
            # Основной queryset для админов
            admin_queryset = Course.objects.filter(school__name=school_name).annotate(
                baselessons_count=Count("sections__lessons")
            )
            # Тестовый курс для всех админов, который нужно добавить
            test_course = Course.objects.filter(course_id=247)
            return admin_queryset | test_course

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
                    When(
                        Exists(Subquery(sub_duration))
                        & GreaterThan(Subquery(sub_duration), 0),
                        then=Subquery(sub_duration),
                    ),
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
                certificate=Subquery(sub_group.values("certificate")[:1]),
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
            school_obj.tariff.name in [TariffPlan.JUNIOR, TariffPlan.MIDDLE]
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
        course_removed = self.request.data.get("course_removed")
        if school and int(school) != school_id:
            return Response(
                "Указанный id школы не соответствует id текущей школы.",
                status=status.HTTP_400_BAD_REQUEST,
            )
        folder = self.request.data.get("folder")

        if folder and folder != "-1":
            folders = Folder.objects.filter(school__name=school_name)
            try:
                folders.get(pk=folder)
            except folders.model.DoesNotExist:
                raise NotFound("Указанная папка не относится к этой школе.")

        data = request.data.copy()
        instance = self.get_object()

        if folder == "-1":
            instance.folder = None
            instance.save()
            data.pop("folder")

        if course_removed == "null":
            instance.course_removed = None
            instance.save()
            return Response({"status": 200}, status=status.HTTP_200_OK)

        serializer = CourseSerializer(instance, data=data, partial=True)
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

        # Устанавливаем дату удаления курса
        instance.course_removed = timezone.now()
        instance.public = "Н"
        instance.is_catalog = False
        instance.is_direct = False
        instance.save()

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
        sort_by = request.GET.get("sort_by", "date_added")
        sort_order = request.GET.get("sort_order", "desc")
        default_date = datetime(2023, 11, 1, tzinfo=pytz.UTC)
        fields = self.request.GET.getlist("fields")
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
            cleaned_phone = re.sub(r"\D", "", search_value)

            query = (
                Q(students__first_name__icontains=search_value)
                | Q(students__last_name__icontains=search_value)
                | Q(students__email__icontains=search_value)
                | Q(name__icontains=search_value)
            )

            if cleaned_phone:
                query |= Q(students__phone_number__icontains=cleaned_phone)

            queryset = queryset.filter(query)

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
        )

        filtered_active_students = queryset.count()

        if sort_by == "progress":
            for obj in data:
                user_id = obj.get("students__id")
                course_id = obj.get("course_id")

                if user_id and course_id:
                    progress = progress_subquery(user_id, course_id)
                else:
                    progress = None

                obj["progress"] = progress

        if sort_by in [
            "students__last_name",
            "last_name",
            "students__email",
            "name",
            "course_id__name",
            "date_added",
            "date_removed",
            "progress",
            "average_mark",
            "mark_sum",
            "students__date_joined",
        ]:
            if sort_order == "asc":
                if sort_by in ["date_added", "date_removed", "students__date_joined"]:
                    sorted_data = sorted(
                        data,
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
                        data,
                        key=lambda x: x.get(sort_by, 0)
                        if x.get(sort_by) is not None
                        else 0,
                    )
                else:
                    sorted_data = sorted(
                        data,
                        key=lambda x: str(x.get(sort_by, "") or "").lower(),
                    )

            else:
                if sort_by in ["date_added", "date_removed", "last_active"]:
                    sorted_data = sorted(
                        data,
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
                        data,
                        key=lambda x: x.get(sort_by, 0)
                        if x.get(sort_by) is not None
                        else 0,
                        reverse=True,
                    )
                else:
                    sorted_data = sorted(
                        data,
                        key=lambda x: str(x.get(sort_by, "") or "").lower(),
                        reverse=True,
                    )

            paginator = StudentsPagination()

            serialized_data = []
            for item in sorted_data:
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
                                "date_added": item["date_added"],
                                "progress": progress_subquery(
                                    item["students__id"], item["course_id"]
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
                                "date_added": item["date_added"],
                                "progress": 0,
                                "all_active_students": all_active_students,
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
                            "date_added": item["date_added"],
                            "progress": item["progress"],
                            "all_active_students": all_active_students,
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
                            "date_added": item["date_added"],
                            "all_active_students": all_active_students,
                            "filtered_active_students": filtered_active_students,
                            "chat_uuid": UserChat.get_existed_chat_id_by_type(
                                chat_creator=user,
                                reciever=item["students__id"],
                                type="PERSONAL",
                            ),
                        }
                    )
            paginated_data = paginator.paginate_queryset(serialized_data, request)
            pagination_data = {
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": paginated_data,
            }
            return Response(pagination_data)
        else:
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
            cleaned_phone = re.sub(r"\D", "", search_value)

            query = (
                Q(students__first_name__icontains=search_value)
                | Q(students__last_name__icontains=search_value)
                | Q(students__email__icontains=search_value)
                | Q(name__icontains=search_value)
            )

            if cleaned_phone:
                query |= Q(students__phone_number=cleaned_phone)

            queryset = queryset.filter(query)

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
                    "student_id": item["students__id"],
                    "first_name": item["students__first_name"],
                    "last_name": item["students__last_name"],
                    "email": item["students__email"],
                    "phone_number": item["students__phone_number"],
                    "course_name": item["course_id__name"],
                    "group_name": item["name"],
                    "last_active": item["students__date_joined"],
                    "mark_sum": item["mark_sum"],
                    "average_mark": item["average_mark"],
                    "date_added": item["date_added"],
                    "date_removed": item["date_removed"],
                    "progress": progress_subquery(
                        item["students__id"], item["course_id"]
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
        user_email = request.query_params.get("user_email")
        max_id = Course.objects.all().aggregate(Max("course_id"))["course_id__max"]
        max_order = Course.objects.all().aggregate(Max("order"))["order__max"]
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return Response(
                {"detail": "Пользователь с таким email не найден."}, status=404
            )

        user_schools = School.objects.filter(owner=user)
        if not user_schools:
            return Response(
                {"detail": "Пользователь должен быть владельцем хотя бы одной школы."},
                status=400,
            )

        existing_copies = Course.objects.filter(
            name=course.name, school__in=user_schools, is_copy=True
        )

        # Флаг для отслеживания изменений доступа
        access_restored = False

        if existing_copies.exists():
            for copy in existing_copies:
                if not copy.is_access:
                    copy.is_access = True
                    copy.save()
                    access_restored = True

            if access_restored:
                return Response(
                    {"detail": "Доступ к существующей копии курса восстановлен."},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "detail": "У пользователя уже есть копия данного курса с доступом."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            new_course = None
            for school in user_schools:
                new_course = course.make_clone(
                    attrs={
                        "course_id": max_id + 1,
                        "order": max_order + 1,
                        "school": school,
                        "is_copy": True,
                    }
                )

                # Обновление max_id и max_order для следующего клонирования
                max_id += 1
                max_order += 1

            CourseCopy.objects.create(
                course_copy_id=new_course, course_id=course.course_id
            )
            return Response(
                {
                    "detail": "Копирование курса успешно завершено.",
                },
                status=200,
            )
        except Exception as e:
            return Response(
                {"detail": f"Произошла ошибка при клонировании курса. ({e})"},
                status=500,
            )

    @action(detail=True)
    def get_course_copy_owners(self, request, *args, **kwargs):
        """Получение владельцев школ, имеющих копии курса\n
        <h2>/api/${school_name}/courses/${course_id}/get_course_copy_owners/?course_name=название</h2>\n
        Возвращает владельцев школ, у которых есть копии курса с указанным названием."""

        course_name = request.query_params.get("course_name")
        if not course_name:
            return Response({"detail": "Название курса не указано."}, status=400)

        copy_courses = Course.objects.filter(
            name=course_name, is_copy=True, is_access=True
        )
        school_ids = copy_courses.values_list("school", flat=True).distinct()
        schools = School.objects.filter(school_id__in=school_ids)
        owners = schools.values_list("owner", flat=True).distinct()
        owners_info = User.objects.filter(id__in=owners).values("email")

        return Response(list(owners_info))

    @action(detail=True, methods=["patch"])
    def delete_course_access(self, request, *args, **kwargs):
        """Удаление доступа к копиям курса по email и названию курса\n
        <h2>/api/{school_name}/courses/{course_id}/delete/</h2>\n
        Удаление доступа к копиям курса"""

        course_name = request.query_params.get("course_name")
        user_emails = request.query_params.getlist("user_emails")

        if not user_emails or not course_name:
            return Response(
                {"detail": "Не указаны email пользователей или название курса."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated_courses = 0
        not_found_emails = []
        for user_email in user_emails:
            try:
                user = User.objects.get(email=user_email)
            except User.DoesNotExist:
                not_found_emails.append(user_email)
                continue

            user_schools = School.objects.filter(owner=user)
            if not user_schools:
                not_found_emails.append(user_email)
                continue

            courses_to_update = Course.objects.filter(
                name=course_name, is_copy=True, school__in=user_schools
            )

            if courses_to_update.exists():
                updated_courses += courses_to_update.update(is_access=False)

        if not_found_emails:
            return Response(
                {
                    "detail": f'Пользователи с email {", ".join(not_found_emails)} не найдены, либо они не являются владельцами школ.',
                    "updated_courses": updated_courses,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": f"Доступ к курсу успешно удален."}, status=status.HTTP_200_OK
        )

    @action(detail=True)
    def sections(self, request, pk, *args, **kwargs):
        """Данные по всем секциям курс\n
        <h2>/api/{school_name}/courses/{course_id}/sections/</h2>\n
        Данные по всем секциям курса"""

        user = self.request.user
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)
        course = self.get_object()

        # Проверка, если курс является копией
        if course.is_copy:
            try:
                original_course_id = CourseCopy.objects.get(
                    course_copy_id=course.course_id
                )
                original_course = Course.objects.get(
                    course_id=original_course_id.course_id
                )
            except Course.DoesNotExist:
                return Response(
                    {"error": "Оригинальный курс не найден."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            original_course = course

        # Получаем параметр поиска из запроса
        search_query = self.request.GET.get("search_query")

        group = None
        if user.groups.filter(group__name="Student", school=school).exists():
            try:
                group = StudentsGroup.objects.get(students=user, course_id_id=course.pk)

                if course.public != "О":
                    return Response(
                        {
                            "error": "Доступ к курсу временно заблокирован. Обратитесь к администратору"
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

                limit = get_student_training_duration(group, user.id)[0]
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

        queryset = Course.objects.filter(course_id=original_course.course_id)

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
                "submit_homework_to_go_on": group.group_settings.submit_homework_to_go_on,
                "submit_test_to_go_on": group.group_settings.submit_test_to_go_on,
                "success_test_to_go_on": group.group_settings.success_test_to_go_on,
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
                    "order": value["section_order"],
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

            if search_query:
                search_filter = Q(name__icontains=search_query) | Q(
                    blocks__description__icontains=search_query
                )
                a = a.filter(search_filter).distinct()
                b = b.filter(search_filter).distinct()
                c = c.filter(search_filter).distinct()

            for i in enumerate((a, b, c)):
                for obj in i[1]:
                    sended = None
                    if obj in a:
                        sended = UserHomework.objects.filter(
                            homework=obj, user=user
                        ).exists()
                    if obj in c:
                        sended = UserTest.objects.filter(test=obj, user=user).exists()
                    # Получаем все блоки урока, чтобы найти блоки с видео
                    video_blocks = BaseLessonBlock.objects.filter(
                        base_lesson=obj.baselesson_ptr_id, type="video"
                    )
                    video_screenshot = None
                    if video_blocks.exists():
                        # Берем скриншот из первого блока видео
                        video_screenshot = video_blocks.first().video_screenshot

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
                            "sended": sended,
                            "completed": lesson_progress.filter(
                                lesson_id=obj.baselesson_ptr_id, completed=True
                            ).exists(),
                            "video_screenshot": video_screenshot,
                        }
                    )

            if user.groups.filter(group__name="Student", school=school).exists():
                all_section_lessons = result_data["sections"][index]["lessons"]

                homeworks = list(
                    filter(lambda el: el["type"] == "homework", all_section_lessons)
                )
                homework_count = len(homeworks)
                completed_hw_count = len(
                    list(filter(lambda el: el["completed"], homeworks))
                )
                result_data["sections"][index]["homework_count"] = homework_count
                result_data["sections"][index][
                    "completed_hw_count"
                ] = completed_hw_count

                lessons = list(
                    filter(lambda el: el["type"] == "lesson", all_section_lessons)
                )
                lesson_count = len(lessons)
                completed_les_count = len(
                    list(filter(lambda el: el["viewed"], lessons))
                )
                result_data["sections"][index]["lesson_count"] = lesson_count
                result_data["sections"][index][
                    "completed_les_count"
                ] = completed_les_count

                tests = list(
                    filter(lambda el: el["type"] == "test", all_section_lessons)
                )
                test_count = len(tests)
                completed_test_count = len(
                    list(filter(lambda el: el["completed"], tests))
                )
                result_data["sections"][index]["test_count"] = test_count
                result_data["sections"][index][
                    "completed_test_count"
                ] = completed_test_count

                result_data["sections"][index]["completed_count"] = (
                    completed_hw_count + completed_les_count + completed_test_count
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

    @transaction.atomic
    @action(detail=False, methods=["POST"])
    def create_courses_fully(self, request, *args, **kwargs):
        """Создание курсов с модулями и уроками\n
        <h2>/api/{school_name}/courses/create_courses_fully/</h2>\n
        Создание курсов с модулями и уроками"""

        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)
        courses_data = request.data.get("courses", [])
        with transaction.atomic():
            for course_data in courses_data:
                course = Course.objects.create(
                    school=school,
                    name=course_data["name"],
                    description=course_data["description"],
                    public=Public.PUBLISHED,
                    is_catalog=True,
                )
                for section_data in course_data["sections"]:
                    section = Section.objects.create(
                        course=course, name=section_data["title"]
                    )
                    for lesson_data in section_data["lessons"]:
                        Lesson.objects.create(
                            section=section, name=lesson_data, active=True
                        )

        return Response("Курсы созданы")


CourseViewSet = apply_swagger_auto_schema(
    tags=["courses"], excluded_methods=["partial_update", "update"]
)(CourseViewSet)
