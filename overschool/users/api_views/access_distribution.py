from datetime import datetime

from chats.models import UserChat, Chat
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import (
    Course,
    LessonAvailability,
    LessonEnrollment,
    StudentsGroup,
    StudentsHistory,
)
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http import HttpResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions
from rest_framework.parsers import MultiPartParser
from schools.models import School, Tariff, TariffPlan
from schools.school_mixin import SchoolMixin
from users.models import UserGroup
from users.serializers import AccessDistributionSerializer
from users.services import SenderServiceMixin

sender_service = SenderServiceMixin()

User = get_user_model()


class AccessDistributionView(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, generics.GenericAPIView
):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AccessDistributionSerializer
    parser_classes = (MultiPartParser,)

    def get_school(self):
        school_name = self.kwargs.get("school_name")
        return School.objects.get(name=school_name)

    def check_existing_role(self, user, school, group):
        return (
            UserGroup.objects.filter(user=user, school=school)
            .exclude(group=group)
            .exists()
        )

    def check_user_existing_roles(self, user, school):
        try:
            return user.groups.filter(school=school).exists()
        except:
            return None

    def handle_existing_roles(self, user, school, group):
        return HttpResponse(
            f"Пользователь уже имеет другую роль в этой школе (email={user.email})",
            status=400,
        )

    def create_user_group(self, user, group, school):
        user_group = user.groups.create(group=group, school=school)
        self.send_email_notification(user.email, group.name, school.name)
        return user_group

    def send_email_notification(self, email, group_name, school_name):
        url = "https://overschool.by/login/"
        subject = "Добавление в группу"
        message = f"Вы были добавлены в группу {group_name} в школе {school_name}. Перейдите по ссылке {url}"
        sender_service.send_code_by_email(email=email, subject=subject, message=message)

    def validate_tariff_plan(self, new_user_count, role):
        school = self.get_school()

        if role == "Student":
            # Получение текущей даты и времени
            current_datetime = datetime.now()
            current_month = current_datetime.month
            current_year = current_datetime.year

            student_count_by_month = UserGroup.objects.filter(
                group__name="Student",
                school=school,
                created_at__year=current_year,
                created_at__month=current_month,
            ).count()

            if (
                student_count_by_month + new_user_count
                > school.tariff.students_per_month
            ):
                return (
                    False,
                    "Превышено количество новых учеников в месяц для выбранного тарифа",
                )

            if school.tariff.name == TariffPlan.INTERN:
                student_count = UserGroup.objects.filter(
                    group__name="Student", school=school
                ).count()
                if student_count + new_user_count > school.tariff.total_students:
                    return False, "Превышено количество учеников для выбранного тарифа"

        elif role in ["Teacher", "Admin"]:
            staff_count = UserGroup.objects.filter(
                group__name__in=["Teacher", "Admin"], school=school
            ).count()
            if (
                school.tariff.name
                in [TariffPlan.INTERN, TariffPlan.JUNIOR, TariffPlan.MIDDLE]
                and staff_count + new_user_count > school.tariff.number_of_staff
            ):
                return False, "Превышено количество cотрудников для выбранного тарифа"

        return True, None

    def handle_teacher_group_fk(self, user, student_groups):
        for student_group in student_groups:
            previous_teacher = student_group.teacher_id
            chat = student_group.chat
            previous_chat = UserChat.objects.filter(
                user=previous_teacher, chat=chat
            ).first()
            if previous_chat:
                previous_chat.delete()
            user.teacher_group_fk.add(student_group)
            UserChat.objects.create(user=user, chat=chat, user_role="Teacher")

    def handle_students_group_fk(self, user, student_groups):
        for student_group in student_groups:
            user.students_group_fk.add(student_group)
            StudentsHistory.objects.create(user=user, students_group=student_group)

            unavailable_lessons = list(
                LessonEnrollment.objects.filter(student_group=student_group).values(
                    "lesson_id"
                )
            )
            unavailable_lessons = list(
                map(lambda el: el["lesson_id"], unavailable_lessons)
            )
            for lesson in unavailable_lessons:
                LessonAvailability.objects.update_or_create(
                    student=user, lesson_id=lesson, defaults={"available": False}
                )

            try:
                chat = student_group.chat
                chat_exists = UserChat.objects.filter(
                    user=user, chat=chat, user_role="Student"
                ).exists()
                if not chat_exists:
                    UserChat.objects.create(user=user, chat=chat, user_role="student")
            except:
                print("Ошибка добавления ученика в чат")

    @swagger_auto_schema(
        request_body=AccessDistributionSerializer,
        tags=["access_distribution"],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_ids = serializer.validated_data.get("user_ids")
        emails = serializer.validated_data.get("emails")
        role = serializer.validated_data.get("role")
        student_groups_ids = serializer.validated_data.get("student_groups")

        school = self.get_school()
        group = Group.objects.get(name=role)

        users_by_id = (
            User.objects.filter(pk__in=user_ids) if user_ids else User.objects.none()
        )
        users_by_email = (
            User.objects.filter(email__in=emails) if emails else User.objects.none()
        )
        users = (users_by_id | users_by_email).distinct()
        new_user_count = users.exclude(groups__school=school).count()

        valid, error_message = self.validate_tariff_plan(new_user_count, role)
        if not valid:
            return HttpResponse(error_message, status=400)

        student_groups = StudentsGroup.objects.none()
        if student_groups_ids:
            student_groups = StudentsGroup.objects.filter(pk__in=student_groups_ids)
            groups_count = student_groups.count()
            courses_count = student_groups.values("course_id").distinct().count()

            if groups_count != courses_count:
                return HttpResponse(
                    "Нельзя преподавать либо учиться в нескольких группах одного и того же курса",
                    status=400,
                )

            if role == "Teacher" and users.count() > 1:
                return HttpResponse(
                    "Нельзя назначить несколько преподавателей в одни и те же группы",
                    status=400,
                )

            for student_group in student_groups:
                if student_group.course_id.school != school:
                    return HttpResponse(
                        "Проверьте принадлежность студенческих групп к вашей школе",
                        status=400,
                    )
                if role == "Teacher" and student_group.type == "WITHOUT_TEACHER":
                    return HttpResponse(
                        "Нельзя назначить преподавателя в группу, не предполагающую наличие преподавателя",
                        status=400,
                    )

        courses_ids = list(
            map(lambda el: el["course_id"], list(student_groups.values("course_id")))
        )

        for user in users:
            if self.check_existing_role(user, school, group):
                return self.handle_existing_roles(user, school, group)

            if not UserGroup.objects.filter(
                user=user, school=school, group=group
            ).exists():
                self.create_user_group(user, group, school)

            if student_groups_ids:
                if role == "Teacher":
                    if user.teacher_group_fk.filter(course_id__in=courses_ids).exists():
                        return HttpResponse(
                            f"Нельзя преподавать в нескольких группах одного и того же курса (email={user.email})",
                            status=400,
                        )
                    self.handle_teacher_group_fk(user, student_groups)
                elif role == "Student":
                    if user.students_group_fk.filter(
                        course_id__in=courses_ids
                    ).exists():
                        return HttpResponse(
                            f"Нельзя учиться в нескольких группах одного и того же курса (email={user.email})",
                            status=400,
                        )
                    self.handle_students_group_fk(user, student_groups)

        return HttpResponse("Доступы предоставлены", status=201)

    @swagger_auto_schema(
        request_body=AccessDistributionSerializer,
        tags=["access_distribution"],
    )
    def delete(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_ids = serializer.validated_data.get("user_ids")
        emails = serializer.validated_data.get("emails")
        users_by_id = (
            User.objects.filter(pk__in=user_ids) if user_ids else User.objects.none()
        )
        users_by_email = (
            User.objects.filter(email__in=emails) if emails else User.objects.none()
        )
        users = (users_by_id | users_by_email).distinct()

        role = serializer.validated_data.get("role")
        student_groups_ids = serializer.validated_data.get("student_groups")
        date = serializer.validated_data.get("date")
        group = Group.objects.get(name=role)
        school = self.get_school()

        student_groups = StudentsGroup.objects.none()
        if student_groups_ids:
            student_groups = StudentsGroup.objects.filter(pk__in=student_groups_ids)
            for student_group in student_groups:
                if student_group.course_id.school != school:
                    return HttpResponse(
                        "Проверьте принадлежность студенческих групп к вашей школе",
                        status=400,
                    )

        for user in users:
            if not user.groups.filter(group=group, school=school).exists():
                return HttpResponse(
                    f"У пользователя нет такой роли в вашей школе (email={user.email})",
                    status=400,
                )
            if not student_groups_ids or role in ["Admin", "Manager"]:
                if (
                    role == "Teacher"
                    and user.teacher_group_fk.filter(course_id__school=school).first()
                ):
                    return HttpResponse(
                        f"Группу нельзя оставить без преподавателя (email={user.email})",
                        status=400,
                    )
                elif role == "Admin" and school.owner == user:
                    return HttpResponse(
                        f"Владельца школы нельзя лишать его прав (email={user.email})",
                        status=400,
                    )
                else:
                    user.groups.get(group=group, school=school).delete()
                    if role == "Student":
                        student_groups = StudentsGroup.objects.filter(
                            students=user, course_id__school=school
                        )
                        for student_group in student_groups:

                            try:
                                history = StudentsHistory.objects.get(
                                    user=user,
                                    students_group=student_group,
                                    is_deleted=False,
                                )
                                if date:
                                    if date < history.date_added:
                                        return HttpResponse(
                                            f"Дата добавления ученика в группу превышает дату удаления его из группы",
                                            status=400,
                                        )
                                    else:
                                        history.date_removed = date
                                else:
                                    history.date_removed = datetime.now()
                                history.is_deleted = True
                                history.save()
                            except:
                                print("Ошибка удаления в StudentsHistory.")

                            try:
                                userchat = UserChat.objects.get(user=user, chat=student_group.chat)
                                if userchat:
                                    userchat.delete()
                            except:
                                print("Ошибка удаления UserChat.")

                            student_group.students.remove(user)

            else:
                if role == "Teacher":
                    return HttpResponse(
                        "Группу нельзя оставить без преподавателя", status=400
                    )
                elif role == "Student":
                    for student_group in student_groups:

                        try:
                            history = StudentsHistory.objects.get(
                                user=user,
                                students_group=student_group,
                                is_deleted=False,
                            )
                            if date:
                                if date < history.date_added:
                                    return HttpResponse(
                                        f"Дата добавления ученика в группу превышает дату удаления его из группы",
                                        status=400,
                                    )
                                else:
                                    history.date_removed = date
                            else:
                                history.date_removed = datetime.now()
                            history.is_deleted = True
                            history.save()
                        except:
                            print("Ошибка удаления в StudentsHistory.")

                        try:
                            userchat = UserChat.objects.get(user=user, chat=student_group.chat)
                            if userchat:
                                userchat.delete()
                        except:
                            print("Ошибка удаления UserChat.")

                        user.students_group_fk.remove(student_group)

                    remaining_groups_count = user.students_group_fk.filter(
                        course_id__school=school
                    ).count()
                    if remaining_groups_count == 0:
                        user.groups.get(group=group, school=school).delete()

        return HttpResponse("Доступ успешно заблокирован", status=201)
