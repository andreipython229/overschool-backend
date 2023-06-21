from common_services.mixins import WithHeadersViewSet
from courses.models import StudentsGroup
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from rest_framework import generics, permissions
from users.serializers import AccessDistributionSerializer

User = get_user_model()


class AccessDistributionView(WithHeadersViewSet, generics.GenericAPIView):
    """Ендпоинт распределения ролей и доступов\n
    Ендпоинт распределения ролей и доступов к группам
    в зависимости от роли пользователя"""

    permission_classes = [permissions.AllowAny]
    serializer_class = AccessDistributionSerializer

    def get_permissions(self):
        permissions = super().get_permissions()
        user = self.request.user
        if user.groups.filter(group__name="Admin").exists():
            return permissions
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data.get("user_id")
        role = serializer.validated_data.get("role")
        student_groups_ids = serializer.validated_data.get("student_groups")

        user = User.objects.get(pk=user_id)
        group = Group.objects.get(name=role)
        if not user.groups.contains(group):
            user.groups.add(group)

        if student_groups_ids:
            student_groups = StudentsGroup.objects.filter(pk__in=student_groups_ids)
            if role == "Teacher":
                for group in student_groups:
                    user.teacher_group_fk.add(group)
            if role == "Student":
                for group in student_groups:
                    user.students_group_fk.add(group)

        return HttpResponse("Доступы предоставлены", status=201)

    def delete(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data.get("user_id")
        role = serializer.validated_data.get("role")
        student_groups_ids = serializer.validated_data.get("student_groups")

        user = User.objects.get(pk=user_id)
        group = Group.objects.get(name=role)

        if not student_groups_ids or role in ["Admin", "Manager"]:
            if not user.groups.contains(group):
                return HttpResponse("У пользователя нет такой роли", status=400)
            elif role == "Teacher" and user.teacher_group_fk.first():
                return HttpResponse(
                    "Группу нельзя оставить без преподавателя", status=400
                )
            else:
                user.groups.remove(group)
                if role == "Student":
                    user.students_group_fk.clear()
                return HttpResponse("Доступ успешно заблокирован", status=201)
        else:
            if role == "Teacher":
                return HttpResponse(
                    "Группу нельзя оставить без преподавателя", status=400
                )
            elif role == "Student":
                student_groups = StudentsGroup.objects.filter(pk__in=student_groups_ids)
                for group in student_groups:
                    user.students_group_fk.remove(group)
                return HttpResponse("Доступ успешно заблокирован", status=201)
