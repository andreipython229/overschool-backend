import json
from datetime import datetime

from chats.models import Chat, UserChat
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import (
    Course,
    LessonAvailability,
    LessonEnrollment,
    StudentsGroup,
    StudentsHistory,
    TrainingDuration,
    UserHomework,
    UserHomeworkCheck,
)
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http import HttpResponse
from django.template.loader import render_to_string
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from schools.models import School, Tariff, TariffPlan
from schools.school_mixin import SchoolMixin
from users.models import UserGroup, UserPseudonym
from users.serializers import AccessDistributionSerializer
from users.services import SenderServiceMixin

sender_service = SenderServiceMixin()

User = get_user_model()


class AccessDistributionView(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, generics.GenericAPIView
):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AccessDistributionSerializer
    parser_classes = (MultiPartParser,)

    def get_school(self):
        school_name = self.kwargs.get("school_name")
        return School.objects.get(name=school_name)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return (
                StudentsGroup.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        # Возвращаем список объектов, связанных с текущей школой
        school = self.get_school()
        return StudentsGroup.objects.filter(course_id__school=school)

    def check_existing_role(self, user, school, group):
        existing_group = (
            UserGroup.objects.filter(user=user, school=school)
            .exclude(group=group)
            .first()
        )
        return existing_group.group.name if existing_group else None

    def check_user_existing_roles(self, user, school):
        try:
            return user.groups.filter(school=school).exists()
        except:
            return None

    def handle_existing_role(self, user, role):
        return HttpResponse(
            f"Пользователь уже имеет другую роль в этой школе (email={user.email});{role}",
            status=400,
        )

    def create_user_group(self, user, group, school, pseudonym):
        if pseudonym:
            UserPseudonym.objects.create(user=user, school=school, pseudonym=pseudonym)
            user_group = user.groups.create(group=group, school=school)
        else:
            user_group = user.groups.create(group=group, school=school)
        return user_group

    def send_email_notification(self, email, course_name, school_name):
        domain = self.request.META.get("HTTP_X_ORIGIN")
        url = f"{domain}/login/"
        subject = "Добавление в группу"
        html_message = render_to_string(
            "added_to_course_template.html",
            {"course_name": course_name, "school_name": school_name, "url": url},
        )
        sender_service.send_code_by_email(
            email=email, subject=subject, message=html_message
        )

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

        elif role in ["Teacher", "Admin"]:
            staff_count = UserGroup.objects.filter(
                group__name__in=["Teacher", "Admin"], school=school
            ).count()
            if (
                school.tariff.name in [TariffPlan.JUNIOR, TariffPlan.MIDDLE]
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

    def handle_students_group_fk(self, user, student_groups, course_name, school):
        for student_group in student_groups:
            user.students_group_fk.add(student_group)
            StudentsHistory.objects.create(user=user, students_group=student_group)

            # Обработка существующих домашних работ
            if student_group.teacher_id:  # Проверяем, есть ли учитель в группе
                existing_homeworks = UserHomework.objects.filter(
                    user=user, homework__section__course=student_group.course_id
                ).prefetch_related("user_homework_checks")

                if existing_homeworks.exists():
                    # Обновляем учителя в домашних работах
                    for homework in existing_homeworks:
                        homework.teacher = student_group.teacher_id
                    UserHomework.objects.bulk_update(existing_homeworks, ["teacher"])

                    # Собираем все проверки домашних работ
                    homework_checks = []
                    for homework in existing_homeworks:
                        homework_checks.extend(
                            homework_check
                            for homework_check in homework.user_homework_checks.all()
                        )

                    # Обновляем автора в проверках домашних работ
                    if homework_checks:
                        for check in homework_checks:
                            check.author = student_group.teacher_id
                        UserHomeworkCheck.objects.bulk_update(
                            homework_checks, ["author"]
                        )

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

            TrainingDuration.objects.update_or_create(
                user=user,
                students_group=student_group,
                defaults={"download": student_group.group_settings.download},
            )

            try:
                chat = student_group.chat
                chat_exists = UserChat.objects.filter(
                    user=user, chat=chat, user_role="Student"
                ).exists()
                if not chat_exists:
                    UserChat.objects.create(user=user, chat=chat, user_role="Student")
            except:
                print("Ошибка добавления ученика в чат")

            self.send_email_notification(user.email, course_name, school.name)

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
        pseudonym = request.data.get("pseudonym")
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
            existing_role = self.check_existing_role(user, school, group)
            if existing_role:
                return self.handle_existing_role(user, existing_role)

            if not UserGroup.objects.filter(
                user=user, school=school, group=group
            ).exists():
                self.create_user_group(user, group, school, pseudonym)

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

                    if student_groups_ids:
                        student_group = StudentsGroup.objects.get(
                            group_id=student_groups_ids[0]
                        )
                        course = Course.objects.get(
                            course_id=student_group.course_id_id
                        )
                        self.handle_students_group_fk(
                            user, student_groups, course.name, school
                        )

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
        pseudonym = request.data.get("pseudonym")
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
                    try:
                        user_pseudonym = UserPseudonym.objects.get(
                            user=user, school=school, pseudonym=pseudonym
                        )
                        user_pseudonym.delete()
                    except UserPseudonym.DoesNotExist:
                        pass
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
                                userchat = UserChat.objects.get(
                                    user=user, chat=student_group.chat
                                )
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
                            userchat = UserChat.objects.get(
                                user=user, chat=student_group.chat
                            )
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

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "user_ids",
                openapi.IN_FORM,
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_INTEGER),
                required=True,
            ),
            openapi.Parameter(
                "role", openapi.IN_FORM, type=openapi.TYPE_STRING, required=True
            ),
            openapi.Parameter(
                "new_group_id",
                openapi.IN_FORM,
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        tags=["access_distribution"],
        operation_description="Update user group",
        consumes=["multipart/form-data"],
    )
    @action(
        detail=True, methods=["patch"], url_path="update-group", url_name="update-group"
    )
    def update_group(self, request, *args, **kwargs):
        id = kwargs.get("pk")
        user_ids = request.data.get("user_ids")
        new_group_id = request.data.get("new_group_id")

        if id is None:
            return Response(
                {"detail": "Идентификатор не предоставлен"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user_ids:
            user_ids = json.loads(user_ids)

        if new_group_id:
            new_group_id = int(new_group_id)

        data = {
            "user_ids": user_ids,
            "role": request.data.get("role"),
            "student_groups": [new_group_id] if new_group_id else [],
        }
        serializer = AccessDistributionSerializer(data=data, partial=True)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_ids = serializer.validated_data.get("user_ids")
        new_group_id = (
            serializer.validated_data.get("student_groups", [])[0]
            if serializer.validated_data.get("student_groups")
            else None
        )

        if not user_ids or new_group_id is None:
            return Response(
                {"detail": "user_ids и student_groups должны быть предоставлены"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        school = self.get_school()

        try:
            new_group = StudentsGroup.objects.get(
                pk=new_group_id, course_id__school=school
            )
        except StudentsGroup.DoesNotExist:
            return Response(
                {"detail": "Группа не найдена или не принадлежит вашей школе"},
                status=status.HTTP_404_NOT_FOUND,
            )

        for user_id in user_ids:
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return Response(
                    {"detail": f"Пользователь с id={user_id} не найден"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Найти текущую группу пользователя в данном курсе
            current_group = user.students_group_fk.filter(
                course_id__school=school
            ).first()

            if current_group:
                # Удалить пользователя из текущей группы
                user.students_group_fk.remove(current_group)

                # Найти чаты пользователя и старого учителя
                user_chats = UserChat.objects.filter(user=user)
                teacher_chats = UserChat.objects.filter(user=current_group.teacher_id)

                for user_chat in user_chats:
                    for teacher_chat in teacher_chats:
                        if user_chat.chat == teacher_chat.chat:
                            # Заменить старого учителя на нового в чате
                            teacher_chat.user = new_group.teacher_id
                            teacher_chat.save()

            # Добавить пользователя в новую группу
            if not user.students_group_fk.filter(
                course_id=new_group.course_id
            ).exists():
                user.students_group_fk.add(new_group)

        return Response({"message": "Группа обновлена"}, status=status.HTTP_200_OK)
