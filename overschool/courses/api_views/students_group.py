from datetime import datetime, timedelta

import pytz
from chats.models import Chat, UserChat
from common_services.apply_swagger_auto_schema import apply_swagger_auto_schema
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import (
    Course,
    GroupCourseAccess,
    Homework,
    Lesson,
    Section,
    SectionTest,
    StudentsGroup,
    TrainingDuration,
)
from courses.models.students.students_group_settings import StudentsGroupSettings
from courses.models.students.students_history import StudentsHistory
from courses.paginators import StudentsPagination, UserHomeworkPagination
from courses.serializers import (
    GroupCourseAccessSerializer,
    MultipleGroupCourseAccessSerializer,
    StudentsGroupSerializer,
    StudentsGroupWTSerializer,
)
from courses.services import get_student_progress
from django.contrib.auth.models import Group
from django.db.models import Avg, Count, F, Q, Sum
from django.shortcuts import get_object_or_404
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from schools.models import School
from schools.school_mixin import SchoolMixin
from users.models import Profile, User, UserGroup
from users.serializers import UserProfileGetSerializer


# Функция возвращает фактическую максимальную продолжительность обучения студента в группе и индивидуально установленную
def get_student_training_duration(group, student_id):
    try:
        training_duration = TrainingDuration.objects.get(
            user_id=student_id, students_group=group
        )
        return (training_duration.limit, training_duration.limit)
    except TrainingDuration.DoesNotExist:
        return (
            (group.training_duration, None) if group.training_duration else (None, None)
        )


class StudentsGroupViewSet(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet
):
    """Эндпоинт получения, создания, изменения групп студентов\n
    <h2>/api/{school_name}/students_group/</h2>\n
    Разрешения для просмотра групп (любой пользователь)
    Разрешения для создания и изменения групп (только пользователи с группой 'Admin')
    """

    serializer_class = StudentsGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = UserHomeworkPagination

    # parser_classes = (MultiPartParser,)

    def get_school(self):
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)
        return school

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return (
                StudentsGroup.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        user = self.request.user
        if user.groups.filter(group__name="Student", school=self.get_school()).exists():
            return StudentsGroup.objects.filter(
                students=user, course_id__school__school_id=self.get_school().school_id
            )
        if user.groups.filter(group__name="Teacher", school=self.get_school()).exists():
            return StudentsGroup.objects.filter(
                teacher_id=user,
                course_id__school__school_id=self.get_school().school_id,
            )
        if user.groups.filter(group__name="Admin", school=self.get_school()).exists():
            return StudentsGroup.objects.filter(
                course_id__school__school_id=self.get_school().school_id
            )

    def get_permissions(self):
        permissions = super().get_permissions()
        user = self.request.user
        school = self.get_school()
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin", school=school).exists():
            return permissions
        if self.action in [
            "list",
            "retrieve",
            "get_students_for_group",
            "user_count_by_month",
            "student_training_duration",
        ]:
            if user.groups.filter(
                group__name__in=["Student", "Teacher"], school=school
            ).exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def perform_create(self, serializer):
        serializer.is_valid()
        course = serializer.validated_data["course_id"]
        school = self.get_school()
        teacher = serializer.validated_data.get("teacher_id")

        if course.school != school:
            raise serializers.ValidationError("Курс не относится к вашей школе.")
        if not teacher.groups.filter(school=school, group__name="Teacher").exists():
            raise serializers.ValidationError(
                "Пользователь, указанный в поле 'teacher_id', не является учителем в вашей школе."
            )

        students = serializer.validated_data.get("students", [])
        # Проверяем, что студенты не дублируются
        if len(students) != len(set(students)):
            raise serializers.ValidationError(
                "Студенты не могут дублироваться в списке."
            )

        for student in students:
            if not student.groups.filter(school=school, group__name="Student").exists():
                raise serializers.ValidationError(
                    "Не все пользователи, добавляемые в группу, являются студентами вашей школы."
                )

        # Создаем чат с названием "Чат с [имя группы]"
        groupname = serializer.validated_data.get("name", "")
        chat_name = f"{groupname}"
        chat = Chat.objects.create(name=chat_name, type="GROUP")

        # Создаём модель настроек группы
        group_settings_data = self.request.data.get("group_settings")
        if not group_settings_data:
            group_settings_data = {}
        group_settings = StudentsGroupSettings.objects.create(**group_settings_data)
        serializer.save(group_settings=group_settings, type="WITH_TEACHER")

        student_group = serializer.save(chat=chat)

        UserChat.objects.create(user=teacher, chat=chat, user_role="Teacher")
        for student in students:
            UserChat.objects.create(user=student, chat=chat, user_role="Student")

        return student_group

    def perform_update(self, serializer):
        course = serializer.validated_data["course_id"]
        school = self.get_school()
        teacher = serializer.validated_data.get("teacher_id")
        name = serializer.validated_data.get("name")

        if course.school != school:
            raise serializers.ValidationError("Курс не относится к вашей школе.")
        if (
            teacher
            and not teacher.groups.filter(school=school, group__name="Teacher").exists()
        ):
            raise serializers.ValidationError(
                "Пользователь, указанный в поле 'teacher_id', не является учителем в вашей школе."
            )

        # Получите текущую группу перед сохранением изменений
        current_group = self.get_object()

        certificate = self.request.data.get("certificate")
        if certificate is not None:
            current_group.certificate = certificate
            current_group.save()

        students = serializer.validated_data.get("students", [])
        group = Group.objects.get(name="Student")

        # Добавляем новых учеников в чат
        for student in students:
            if not student.students_group_fk.filter(pk=current_group.pk).exists():
                if not UserGroup.objects.filter(
                    user=student, group=group, school=school
                ).exists():
                    raise serializers.ValidationError(
                        "Не все пользователи, добавляемые в группу, являются студентами вашей школы."
                    )
        serializer.save()

        # обновляем чат с участниками группы
        chat = current_group.chat
        previous_teacher = current_group.teacher_id

        if current_group.name != name:
            chat.name = name
            chat.save()

        if teacher and not UserChat.objects.filter(user=teacher, chat=chat).exists():
            UserChat.objects.create(user=teacher, chat=chat, user_role="Teacher")
        if teacher and teacher != previous_teacher:
            previous_chat = UserChat.objects.filter(
                user=previous_teacher, chat=chat
            ).first()
            if previous_chat:
                previous_chat.delete()
        for student in students:
            if not UserChat.objects.filter(user=student, chat=chat).exists():
                UserChat.objects.create(user=student, chat=chat, user_role="Student")

    def destroy(self, request, *args, **kwargs):
        current_group = self.get_object()

        if current_group.chat:
            UserChat.objects.filter(chat=current_group.chat).delete()
            current_group.chat.delete()

        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["GET"])
    def get_students_for_group(self, request, pk=None, *args, **kwargs):
        """Все студенты одной группы\n
        <h2>/api/{school_name}/students_group/{group_id}/get_students_for_group/</h2>\n"""
        group = self.get_object()
        user = self.request.user
        school = self.get_school()
        students = group.students.none()
        if user.groups.filter(group__name="Teacher", school=school).exists():
            if group.teacher_id == user:
                students = group.students.all()
        if user.groups.filter(group__name="Admin", school=school).exists():
            students = group.students.all()

        search_value = self.request.GET.get("search_value")
        if search_value:
            students = students.filter(
                Q(first_name__icontains=search_value)
                | Q(last_name__icontains=search_value)
                | Q(email__icontains=search_value)
            )

        # Фильтры
        first_name = self.request.GET.get("first_name")
        if first_name:
            students = students.filter(first_name=first_name)

        last_name = self.request.GET.get("last_name")
        if last_name:
            students = students.filter(last_name=last_name)

        last_active_min = self.request.GET.get("last_active_min")
        if last_active_min:
            last_active_min = datetime.strptime(last_active_min, "%Y-%m-%d")
            students = students.filter(last_login__gte=last_active_min)

        last_active_max = self.request.GET.get("last_active_max")
        if last_active_max:
            last_active_max = datetime.strptime(last_active_max, "%Y-%m-%d")
            last_active_max += timedelta(days=1)
            students = students.filter(last_login__lte=last_active_max)

        last_active = self.request.GET.get("last_active")
        if last_active:
            last_active = datetime.strptime(last_active, "%Y-%m-%d")
            students = students.filter(last_login=last_active)

        mark_sum = self.request.GET.get("mark_sum")
        if mark_sum:
            students = students.annotate(mark_sum=Sum("user_homeworks__mark"))
            students = students.filter(mark_sum=mark_sum)

        average_mark = self.request.GET.get("average_mark")
        if average_mark:
            students = students.annotate(average_mark=Avg("user_homeworks__mark"))
            students = students.filter(average_mark=average_mark)

        mark_sum_min = self.request.GET.get("mark_sum_min")
        if mark_sum_min:
            students = students.annotate(mark_sum=Sum("user_homeworks__mark"))
            students = students.filter(mark_sum__gte=mark_sum_min)

        mark_sum_max = self.request.GET.get("mark_sum_max")
        if mark_sum_max:
            students = students.annotate(mark_sum=Sum("user_homeworks__mark"))
            students = students.filter(mark_sum__lte=mark_sum_max)

        average_mark_min = self.request.GET.get("average_mark_min")
        if average_mark_min:
            students = students.annotate(average_mark=Avg("user_homeworks__mark"))
            students = students.filter(average_mark__gte=average_mark_min)

        average_mark_max = self.request.GET.get("average_mark_max")
        if average_mark_max:
            students = students.annotate(average_mark=Avg("user_homeworks__mark"))
            students = students.filter(average_mark__lte=average_mark_max)

        student_data = []
        for student in students:
            profile = Profile.objects.get(user_id=student)
            serializer = UserProfileGetSerializer(
                profile, context={"request": self.request}
            )
            students_history = StudentsHistory.objects.filter(
                user_id=student.id, students_group=group.group_id, is_deleted=False
            ).first()

            student_data.append(
                {
                    "course_id": group.course_id.course_id,
                    "course_name": group.course_id.name,
                    "group_id": group.group_id,
                    "group_name": group.name,
                    "student_id": student.id,
                    "username": student.username,
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "email": student.email,
                    "school_name": school.name,
                    "avatar": serializer.data["avatar"],
                    "last_active": student.date_joined,
                    "last_login": student.last_login,
                    "mark_sum": student.user_homeworks.aggregate(mark_sum=Sum("mark"))[
                        "mark_sum"
                    ],
                    "average_mark": student.user_homeworks.aggregate(
                        average_mark=Avg("mark")
                    )["average_mark"],
                    "progress": get_student_progress(
                        student.id, group.course_id, group.group_id
                    ),
                    "date_added": students_history.date_added
                    if students_history
                    else None,
                    "chat_uuid": UserChat.get_existed_chat_id_by_type(
                        chat_creator=user, reciever=student.id, type="PERSONAL"
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
                        student_data,
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
                        student_data,
                        key=lambda x: x.get(sort_by, 0)
                        if x.get(sort_by) is not None
                        else 0,
                    )
                else:
                    sorted_data = sorted(
                        student_data,
                        key=lambda x: str(x.get(sort_by, "") or "").lower(),
                    )

            else:
                if sort_by in [
                    "date_added",
                    "date_removed",
                    "last_active",
                ]:
                    sorted_data = sorted(
                        student_data,
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
                        student_data,
                        key=lambda x: x.get(sort_by, 0)
                        if x.get(sort_by) is not None
                        else 0,
                        reverse=True,
                    )
                else:
                    sorted_data = sorted(
                        student_data,
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
    def get_all_students_for_group(self, request, pk=None, *args, **kwargs):
        """Все студенты одной группы без пагинации\n
        <h2>/api/{school_name}/students_group/{group_id}/get_all_students_for_group/</h2>\n"""
        group = self.get_object()
        user = self.request.user
        school = self.get_school()
        students = group.students.none()
        if user.groups.filter(group__name="Teacher", school=school).exists():
            if group.teacher_id == user:
                students = group.students.all()
        if user.groups.filter(group__name="Admin", school=school).exists():
            students = group.students.all()

        search_value = self.request.GET.get("search_value")
        if search_value:
            students = students.filter(
                Q(first_name__icontains=search_value)
                | Q(last_name__icontains=search_value)
                | Q(email__icontains=search_value)
            )

        # Фильтры
        first_name = self.request.GET.get("first_name")
        if first_name:
            students = students.filter(first_name=first_name)

        last_name = self.request.GET.get("last_name")
        if last_name:
            students = students.filter(last_name=last_name)

        last_active_min = self.request.GET.get("last_active_min")
        if last_active_min:
            students = students.filter(date_joined__gte=last_active_min)

        last_active_max = self.request.GET.get("last_active_max")
        if last_active_max:
            students = students.filter(date_joined__lte=last_active_max)

        last_active = self.request.GET.get("last_active")
        if last_active:
            students = students.filter(date_joined=last_active)

        mark_sum = self.request.GET.get("mark_sum")
        if mark_sum:
            students = students.annotate(mark_sum=Sum("user_homeworks__mark"))
            students = students.filter(mark_sum=mark_sum)

        average_mark = self.request.GET.get("average_mark")
        if average_mark:
            students = students.annotate(average_mark=Avg("user_homeworks__mark"))
            students = students.filter(average_mark=average_mark)

        mark_sum_min = self.request.GET.get("mark_sum_min")
        if mark_sum_min:
            students = students.annotate(mark_sum=Sum("user_homeworks__mark"))
            students = students.filter(mark_sum__gte=mark_sum_min)

        mark_sum_max = self.request.GET.get("mark_sum_max")
        if mark_sum_max:
            students = students.annotate(mark_sum=Sum("user_homeworks__mark"))
            students = students.filter(mark_sum__lte=mark_sum_max)

        average_mark_min = self.request.GET.get("average_mark_min")
        if average_mark_min:
            students = students.annotate(average_mark=Avg("user_homeworks__mark"))
            students = students.filter(average_mark__gte=average_mark_min)

        average_mark_max = self.request.GET.get("average_mark_max")
        if average_mark_max:
            students = students.annotate(average_mark=Avg("user_homeworks__mark"))
            students = students.filter(average_mark__lte=average_mark_max)

        student_data = []
        for student in students:
            profile = Profile.objects.get(user_id=student)
            serializer = UserProfileGetSerializer(
                profile, context={"request": self.request}
            )
            students_history = StudentsHistory.objects.filter(
                user_id=student.id, students_group=group.group_id, is_deleted=False
            ).first()

            student_data.append(
                {
                    "course_id": group.course_id.course_id,
                    "course_name": group.course_id.name,
                    "group_id": group.group_id,
                    "group_name": group.name,
                    "student_id": student.id,
                    "username": student.username,
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "email": student.email,
                    "school_name": school.name,
                    "avatar": serializer.data["avatar"],
                    "last_active": student.date_joined,
                    "last_login": student.last_login,
                    "mark_sum": student.user_homeworks.aggregate(mark_sum=Sum("mark"))[
                        "mark_sum"
                    ],
                    "average_mark": student.user_homeworks.aggregate(
                        average_mark=Avg("mark")
                    )["average_mark"],
                    "progress": get_student_progress(
                        student.id, group.course_id, group
                    ),
                    "date_added": students_history.date_added
                    if students_history
                    else None,
                    "progress": get_student_progress(
                        student.id, group.course_id, group.group_id
                    ),
                    "date_added": students_history.date_added
                    if students_history
                    else None,
                    "chat_uuid": UserChat.get_existed_chat_id_by_type(
                        chat_creator=user, reciever=student.id, type="PERSONAL"
                    ),
                }
            )

        return Response(student_data)

    @action(detail=True, methods=["GET"])
    def section_student_group(self, request, pk=None, *args, **kwargs):
        group = self.get_object()
        sections_data = self.get_group_sections_and_availability(group)
        response_data = {
            "group_id": group.group_id,
            "sections": sections_data,
        }
        return Response(response_data)

    def get_group_sections_and_availability(self, group):
        course = group.course_id
        sections = Section.objects.filter(course=course)
        sections_data = []
        for section in sections:
            lessons_data = []
            for lesson in section.lessons.all():
                availability = lesson.is_available_for_group(group.group_id)

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
                    "order": lesson.order,
                }
                lessons_data.append(lesson_data)

            lessons_data.sort(key=lambda x: x["order"])

            section_data = {
                "section_id": section.section_id,
                "name": section.name,
                "lessons": lessons_data,
            }
            sections_data.append(section_data)

        return sections_data

    @action(detail=True)
    def user_count_by_month(self, request, pk, *args, **kwargs):
        """Кол-во новых пользователей группы за месяц\n
        <h2>/api/{school_name}/students_group/{group_id}/user_count_by_month/</h2>\n
        по дефолту стоит текущий месяц,
        для конкретного месяца указываем параметр month_number="""

        queryset = StudentsGroup.objects.none()
        user = self.request.user
        group = self.get_object()
        school = self.get_school()
        if user.groups.filter(
            group__name__in=["Admin", "Teacher"], school=school
        ).exists():
            queryset = StudentsGroup.objects.filter(group_id=group.pk)

        month_number = request.GET.get("month_number", datetime.now().month)
        queryset = queryset.filter(students__date_joined__month=month_number)

        datas = queryset.values(group=F("group_id")).annotate(
            students_sum=Count("students__id")
        )

        for data in datas:
            data["graphic_data"] = queryset.values(
                group=F("group_id"), date=F("students__date_joined__day")
            ).annotate(students_sum=Count("students__id"))

        page = self.paginate_queryset(datas)
        if page is not None:
            return self.get_paginated_response(page)
        return Response(datas)

    @action(detail=True, methods=["GET"])
    def student_training_duration(self, request, *args, **kwargs):
        group = self.get_object()
        student_id = request.query_params.get("student_id", None)
        if not student_id:
            return Response(
                {"error": "Не указан ID студента"}, status=status.HTTP_400_BAD_REQUEST
            )
        user = self.request.user
        if user.groups.filter(group__name="Student", school=self.get_school()).exists():
            if int(student_id) != user.id:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if not group.students.filter(id=student_id).exists():
            return Response(
                {"error": "Указанный студент не учится в этой группе"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        limit = get_student_training_duration(group, student_id)

        return Response(
            {"final_limit": limit[0], "individual_limit": limit[1]},
            status=status.HTTP_200_OK,
        )


StudentsGroupViewSet = apply_swagger_auto_schema(
    tags=[
        "students_group",
    ]
)(StudentsGroupViewSet)


class StudentsGroupWithoutTeacherViewSet(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet
):
    serializer_class = StudentsGroupWTSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = UserHomeworkPagination

    def get_school(self):
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)
        return school

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return StudentsGroup.objects.none()
        user = self.request.user
        if user.groups.filter(group__name="Student", school=self.get_school()).exists():
            return StudentsGroup.objects.filter(
                students=user, course_id__school__school_id=self.get_school().school_id
            )
        if user.groups.filter(group__name="Admin", school=self.get_school()).exists():
            return StudentsGroup.objects.filter(
                course_id__school__school_id=self.get_school().school_id
            )

    def get_permissions(self):
        permissions = super().get_permissions()
        user = self.request.user
        school = self.get_school()
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin", school=school).exists():
            return permissions
        if self.action in [
            "list",
            "retrieve",
            "get_students_for_group",
            "user_count_by_month",
        ]:
            if user.groups.filter(group__name__in=["Student"], school=school).exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def perform_create(self, serializer):
        serializer.is_valid()
        course = serializer.validated_data["course_id"]
        type = serializer.validated_data["type"]
        school = self.get_school()

        if course.school != school:
            raise serializers.ValidationError("Курс не относится к вашей школе.")

        students = serializer.validated_data.get("students", [])

        # Проверяем, что студенты не дублируются
        if len(students) != len(set(students)):
            raise serializers.ValidationError(
                "Студенты не могут дублироваться в списке."
            )

        for student in students:
            if not student.groups.filter(school=school, group__name="Student").exists():
                raise serializers.ValidationError(
                    "Не все пользователи, добавляемые в группу, являются студентами вашей школы."
                )

        group_settings_data = self.request.data.get("group_settings")
        if not group_settings_data:
            group_settings_data = {}
        group_settings = StudentsGroupSettings.objects.create(**group_settings_data)
        # Создаем чат с названием "Чат с [имя группы]"
        groupname = serializer.validated_data.get("name", "")
        chat_name = f"{groupname}"
        chat = Chat.objects.create(name=chat_name, type="GROUP")

        serializer.save(group_settings=group_settings, type=type)
        student_group = serializer.save(chat=chat, user=self.request.user)

        admins = User.objects.filter(
            groups__school=student_group.course_id.school,
            groups__group__name__in=["Admin"],
        )
        # UserChat.objects.create(user=self.request.user, chat=chat, user_role="Admin")
        for admin in admins:
            if not UserChat.objects.filter(
                user=admin, chat=chat, user_role="Admin"
            ).exists():
                UserChat.objects.create(user=admin, chat=chat, user_role="Admin")

        return student_group

    def perform_update(self, serializer):
        course = serializer.validated_data["course_id"]
        school = self.get_school()
        students = serializer.validated_data.get("students", [])
        teacher = serializer.validated_data.get("teacher_id")

        if course.school != school:
            raise serializers.ValidationError("Курс не относится к вашей школе.")

        current_group = self.get_object()

        chat = current_group.chat
        previous_teacher = current_group.teacher_id

        if teacher and not UserChat.objects.filter(user=teacher, chat=chat).exists():
            UserChat.objects.create(user=teacher, chat=chat, user_role="Teacher")
            current_group.teacher_id = teacher

        if teacher and teacher != previous_teacher:
            previous_chat = UserChat.objects.filter(
                user=previous_teacher, chat=chat
            ).first()
            if previous_chat:
                previous_chat.delete()

        for student in students:
            if not UserChat.objects.filter(user=student, chat=chat).exists():
                UserChat.objects.create(user=student, chat=chat, user_role="Student")
                current_group.students.add(student)

        current_group.save()
        serializer.save()


class GroupCourseAccessViewSet(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet
):
    """Эндпоинт получения, создания, удаления разрешений к курсам\n
    <h2>/api/{school_name}/group_course_access/</h2>\n
    Разрешения (только пользователи с группой 'Admin')
    """

    serializer_class = GroupCourseAccessSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "head", "post", "delete", "options"]

    def get_school(self):
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)
        return school

    def get_permissions(self):
        permissions = super().get_permissions()
        user = self.request.user
        school = self.get_school()
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin", school=school).exists():
            return permissions
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return GroupCourseAccess.objects.none()
        user = self.request.user

        if user.groups.filter(group__name="Admin", school=self.get_school()).exists():
            return GroupCourseAccess.objects.filter(
                course_id__school__school_id=self.get_school().school_id
            )

    def get_serializer_class(self):
        if self.action == "create" or self.action == "perform_create":
            return MultipleGroupCourseAccessSerializer
        return GroupCourseAccessSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        # Проверка администратора школы и связь с курсами групп
        group_course_access_objects = []
        for data in serializer.validated_data:
            group_obj = get_object_or_404(StudentsGroup, group_id=data["group"])
            course_obj = get_object_or_404(Course, course_id=data["course"])
            if (
                not group_obj.course_id.school == self.get_school()
                or not course_obj.school == self.get_school()
            ):
                return Response(
                    {
                        "detail": "Вы не можете назначать разрешения для групп или курсов других школ"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            group_course_access_objects.append(
                GroupCourseAccess(group=group_obj, course=course_obj)
            )

        GroupCourseAccess.objects.bulk_create(group_course_access_objects)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Проверка принадлежности группы и курса к школе текущего администратора
        if (
            not instance.group.course_id.school == self.get_school()
            or not instance.course.school == self.get_school()
        ):
            return Response(
                {
                    "detail": "Вы не можете удалять разрешения для групп или курсов других школ"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
