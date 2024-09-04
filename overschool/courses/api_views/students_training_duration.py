from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.api_views.schemas import StudentProgressSchemas
from courses.models import StudentsGroup, TrainingDuration
from courses.serializers import TrainingDurationSerializer
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from schools.models import School
from schools.school_mixin import SchoolMixin
from users.models import User


class TrainingDurationViewSet(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet
):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TrainingDurationSerializer
    http_method_names = ["post", "get"]

    def get_school(self):
        school_name = self.kwargs.get("school_name")
        return School.objects.get(name=school_name)

    def get_permissions(self, *args, **kwargs):
        permissions = super().get_permissions()
        user = self.request.user
        school = self.get_school()
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin", school=school).exists():
            return permissions
        if self.action in ["list", "retrieve"]:
            if user.groups.filter(
                group__name__in=["Student", "Teacher"], school=school
            ).exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return (
                TrainingDuration.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        user = self.request.user
        school = self.get_school()
        if user.groups.filter(group__name="Admin", school=school).exists():
            return TrainingDuration.objects.filter(
                students_group__course_id__school=school
            )
        if user.groups.filter(group__name="Teacher", school=school).exists():
            return TrainingDuration.objects.filter(
                students_group__course_id__school=school,
                students_group__teacher_id=user,
            )
        if user.groups.filter(group__name="Student", school=school).exists():
            return TrainingDuration.objects.filter(
                students_group__course_id__school=school, user=user
            )

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        student = serializer.validated_data.get("user")
        students_group = serializer.validated_data.get("students_group")

        if students_group.course_id.school != self.get_school():
            return Response(
                f"В вашей школе такая группа не найдена.",
                status=status.HTTP_403_FORBIDDEN,
            )
        if not student.students_group_fk.filter(
            group_id=students_group.group_id
        ).exists():
            return Response(
                f"Такой ученик не учится в этой группе.",
                status=status.HTTP_403_FORBIDDEN,
            )

        training_duration = TrainingDuration.objects.filter(
            user=student, students_group=students_group
        ).first()

        if training_duration:
            limit = serializer.validated_data.get("limit")
            if limit is not None:
                training_duration.limit = limit
            if request.data.get("download") is not None:
                training_duration.download = serializer.validated_data.get("download")
            training_duration.save()
        else:
            serializer.save()

        return HttpResponse(
            "Продолжительность обучения и иные особенности установлены", status=201
        )
