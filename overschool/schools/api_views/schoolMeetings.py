from django.db.models import Q
from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied

from courses.models.students.students_group import StudentsGroup
from schools.models import SchoolMeetings, School
from schools.school_mixin import SchoolMixin
from schools.serializers import SchoolMeetingsSerializer


class SchoolMeetingsViewSet(viewsets.ModelViewSet, SchoolMixin):
    serializer_class = SchoolMeetingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_school(self):
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)
        return school

    def get_queryset(self, *args, **kwargs):
        if getattr(self, "swagger_fake_view", False):
            return (
                SchoolMeetings.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        user = self.request.user
        school = self.get_school()
        if user.groups.filter(group__name="Admin", school=school).exists():
            return SchoolMeetings.objects.filter(students_groups__course_id__school_id=school).distinct()
        student_groups = StudentsGroup.objects.filter(students=user)
        teacher_groups = StudentsGroup.objects.filter(teacher_id=user)

        return SchoolMeetings.objects.filter(
            Q(students_groups__in=student_groups) | Q(students_groups__in=teacher_groups)
        ).distinct()


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
        ]:
            if user.groups.filter(
                    group__name__in=["Student", "Teacher"], school=school
            ).exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    class Meta:
        model = SchoolMeetings
        fields = '__all__'
