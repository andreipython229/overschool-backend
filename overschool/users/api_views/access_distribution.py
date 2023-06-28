from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import StudentsGroup
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from rest_framework import generics, permissions
from schools.models import School
from schools.school_mixin import SchoolMixin
from users.serializers import AccessDistributionSerializer

User = get_user_model()


class AccessDistributionView(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, generics.GenericAPIView
):
    """Ендпоинт распределения ролей и доступов\n
    Ендпоинт распределения ролей и доступов к группам
    в зависимости от роли пользователя"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AccessDistributionSerializer

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

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data.get("user_id")
        role = serializer.validated_data.get("role")
        student_groups_ids = serializer.validated_data.get("student_groups")

        user = User.objects.get(pk=user_id)
        group = Group.objects.get(name=role)
        school = self.get_school()
        if not user.groups.filter(group=group, school=school).exists():
            user.groups.create(group=group, school=school)

        if student_groups_ids:
            student_groups = StudentsGroup.objects.filter(pk__in=student_groups_ids)
            groups_count = student_groups.count()
            courses_count = student_groups.values("course_id").distinct().count()
            if groups_count != courses_count:
                return HttpResponse(
                    "Нельзя преподавать либо учиться в нескольких группах одного и того же курса",
                    status=400,
                )
            for group in student_groups:
                if group.course_id.school != school:
                    return HttpResponse(
                        "Проверьте принадлежность студенческих групп к вашей школе",
                        status=400,
                    )
            if role == "Teacher":
                if user.students_group_fk.filter(pk__in=student_groups_ids).exists():
                    return HttpResponse(
                        "Преподавателем группы не может стать студент данной группы",
                        status=400,
                    )
                else:
                    for group in student_groups:
                        user.teacher_group_fk.add(group)
            if role == "Student":
                if user.teacher_group_fk.filter(pk__in=student_groups_ids).exists():
                    return HttpResponse(
                        "Студентом группы не может быть преподаватель данной группы",
                        status=400,
                    )
                else:
                    for group in student_groups:
                        user.students_group_fk.add(group)

        return HttpResponse("Доступы предоставлены", status=201)

    def delete(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data.get("user_id")
        role = serializer.validated_data.get("role")
        student_groups_ids = serializer.validated_data.get("student_groups")

        user = User.objects.get(pk=user_id)
        group = Group.objects.get(name=role)
        school = self.get_school()

        if not user.groups.filter(group=group, school=school).exists():
            return HttpResponse(
                "У пользователя нет такой роли в вашей школе", status=400
            )
        if not student_groups_ids or role in ["Admin", "Manager"]:
            if (
                role == "Teacher"
                and user.teacher_group_fk.filter(course_id__school=school).first()
            ):
                return HttpResponse(
                    "Группу нельзя оставить без преподавателя", status=400
                )
            else:
                user.groups.get(group=group, school=school).delete()
                if role == "Student":
                    user.students_group_fk.filter(course_id__school=school).delete()
                return HttpResponse("Доступ успешно заблокирован", status=201)
        else:
            if role == "Teacher":
                return HttpResponse(
                    "Группу нельзя оставить без преподавателя", status=400
                )
            elif role == "Student":
                student_groups = StudentsGroup.objects.filter(pk__in=student_groups_ids)
                for group in student_groups:
                    if group.course_id.school != school:
                        return HttpResponse(
                            "Проверьте принадлежность студенческих групп к вашей школе",
                            status=400,
                        )
                for group in student_groups:
                    user.students_group_fk.remove(group)
                return HttpResponse("Доступ успешно заблокирован", status=201)
