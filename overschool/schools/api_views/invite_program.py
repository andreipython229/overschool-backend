from rest_framework import permissions, viewsets, status
from common_services.mixins import WithHeadersViewSet
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from schools.models import School
from courses.models.students.students_group import StudentsGroup
from schools.models import InviteProgram
from schools.school_mixin import SchoolMixin
from schools.serializers import InviteProgramSerializer


class InviteProgramViewSet(WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InviteProgramSerializer

    def get_permissions(self):
        """Определяет доступ на основе роли пользователя"""
        school_name = self.kwargs.get("school_name")
        school = get_object_or_404(School, name=school_name)
        user = self.request.user

        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

        # Администраторы школы могут управлять программой
        if user.groups.filter(group__name="Admin", school=school).exists():
            return super().get_permissions()

        # Студенты могут только просматривать активные программы
        if self.action in ["list", "retrieve"]:
            if user.groups.filter(group__name__in=["Student", "Teacher"], school=school).exists():
                return super().get_permissions()

        raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_queryset(self):
        """Возвращает активные инвайт-программы для школы"""
        if getattr(self, "swagger_fake_view", False):
            return (
                InviteProgram.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        school_name = self.kwargs.get("school_name")
        school = get_object_or_404(School, name=school_name)
        user = self.request.user

        if user.groups.filter(group__name="Admin", school=school).exists():
            return InviteProgram.objects.filter(school=school)

        if user.groups.filter(group__name__in=["Student", "Teacher"], school=school).exists():
            return InviteProgram.objects.filter(school=school, is_active=True, groups__in=user.students_group_fk.all())

        return InviteProgram.objects.none()

    def list(self, request, *args, **kwargs):
        """Студентам возвращаем только активную программу, если они в группе"""
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response([])

        user = request.user
        if user.groups.filter(group__name="Student").exists():
            queryset = queryset.filter(is_active=True).distinct()
            if queryset.exists():
                return Response(self.get_serializer(queryset.first()).data)

        return Response(self.get_serializer(queryset, many=True).data)

    def create(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school = get_object_or_404(School, name=school_name)

        if InviteProgram.objects.filter(school=school).exists():
            return Response(
                {"detail": "У школы уже есть инвайт-программа."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().create(request, *args, **kwargs)

    def perform_update(self, serializer):
        school_name = self.kwargs.get("school_name")
        school = get_object_or_404(School, name=school_name)

        serializer.save(school=school)
