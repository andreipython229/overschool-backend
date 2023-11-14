from datetime import datetime

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import StudentsGroup
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions
from rest_framework.parsers import MultiPartParser
from schools.models import School, TariffPlan
from schools.school_mixin import SchoolMixin
from users.models import UserGroup, UserRole
from users.serializers import AccessDistributionSerializer

User = get_user_model()


class AccessDistributionView(
    LoggingMixin,
    WithHeadersViewSet,
    SchoolMixin,
    generics.GenericAPIView,
):
    """Ендпоинт распределения ролей и доступов\n
    <h2>/api/{school_name}/access-distribution/</h2>\n
    Ендпоинт распределения ролей и доступов к группам
    в зависимости от роли пользователя"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AccessDistributionSerializer
    parser_classes = (MultiPartParser,)

    def get_school(self):
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)
        return school

    def get_permissions(self):
        permissions = super().get_permissions()
        user = self.request.user

        if user.groups.filter(school=self.get_school(), group__name="Admin").exists():
            return permissions
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    @swagger_auto_schema(
        request_body=AccessDistributionSerializer,
        tags=["access_distribution"],
    )
    def post(self, request, *args, **kwargs):
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
        group = Group.objects.get(name=role)
        school = self.get_school()

        new_user_count = users.exclude(groups__school=school).count()

        # Получение текущей даты и времени
        current_datetime = datetime.now()
        current_month = current_datetime.month
        current_year = current_datetime.year
        if role == "Student":
            if school.tariff.name == TariffPlan.INTERN:
                student_count_by_month = UserGroup.objects.filter(
                    group__name="Student",
                    school=school,
                    created_at__year=current_year,
                    created_at__month=current_month,
                ).count()
                if (
                    school.tariff.students_per_month - student_count_by_month
                    < new_user_count
                ):
                    return HttpResponse(
                        f"Превышено количество новых учеников в месяц для выбранного тарифа. Можно добавить новых учеников: {school.tariff.students_per_month - student_count_by_month}",
                        status=400,
                    )
                student_count = UserGroup.objects.filter(
                    group__name="Student", school=school
                ).count()
                if school.tariff.total_students - student_count < new_user_count:
                    return HttpResponse(
                        f"Превышено количество учеников для выбранного тарифа. Можно добавить новых учеников: {school.tariff.total_students - student_count}",
                        status=400,
                    )
            elif school.tariff.name in [
                TariffPlan.JUNIOR,
                TariffPlan.MIDDLE,
                TariffPlan.SENIOR,
            ]:
                student_count_by_month = UserGroup.objects.filter(
                    group__name="Student",
                    school=school,
                    created_at__year=current_year,
                    created_at__month=current_month,
                ).count()
                if (
                    school.tariff.students_per_month - student_count_by_month
                    < new_user_count
                ):
                    return HttpResponse(
                        "Превышено количество новых учеников в месяц для выбранного тарифа",
                        status=400,
                    )
        elif role in ["Teacher", "Admin"]:
            staff_count = UserGroup.objects.filter(
                group__name__in=["Teacher", "Admin"], school=school
            ).count()
            if (
                school.tariff.name
                in [TariffPlan.INTERN, TariffPlan.JUNIOR, TariffPlan.MIDDLE]
                and school.tariff.number_of_staff - staff_count < new_user_count
            ):
                return HttpResponse(
                    "Превышено количество cотрудников для выбранного тарифа",
                    status=400,
                )

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
            for student_group in student_groups:
                if student_group.course_id.school != school:
                    return HttpResponse(
                        "Проверьте принадлежность студенческих групп к вашей школе",
                        status=400,
                    )
        courses_ids = list(
            map(lambda el: el["course_id"], list(student_groups.values("course_id")))
        )

        for user in users:
            # Проверка на то что у пользователя в этой школе уже есть роль
            if (
                UserGroup.objects.filter(user=user, school=school)
                .exclude(group=group)
                .exists()
            ):
                return HttpResponse(
                    f"Пользователь уже имеет другую роль в этой школе (email={user.email})",
                    status=400,
                )

            if not user.groups.filter(group=group, school=school).exists():
                user.groups.create(group=group, school=school)

            if student_groups_ids:
                if role == "Teacher":
                    if user.teacher_group_fk.filter(course_id__in=courses_ids).exists():
                        return HttpResponse(
                            f"Нельзя преподавать в нескольких группах одного и того же курса (email={user.email})",
                            status=400,
                        )
                    for student_group in student_groups:
                        user.teacher_group_fk.add(student_group)
                if role == "Student":
                    if user.students_group_fk.filter(
                        course_id__in=courses_ids
                    ).exists():
                        return HttpResponse(
                            f"Нельзя учиться в нескольких группах одного и того же курса (email={user.email})",
                            status=400,
                        )
                    for student_group in student_groups:
                        user.students_group_fk.add(student_group)

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
                            student_group.students.remove(user)
            else:
                if role == "Teacher":
                    return HttpResponse(
                        "Группу нельзя оставить без преподавателя", status=400
                    )
                elif role == "Student":
                    for student_group in student_groups:
                        user.students_group_fk.remove(student_group)

        return HttpResponse("Доступ успешно заблокирован", status=201)
