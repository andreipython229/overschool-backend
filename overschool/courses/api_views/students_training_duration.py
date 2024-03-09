from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.api_views.schemas import StudentProgressSchemas
from courses.models import StudentsGroup, TrainingDuration
from courses.serializers import TrainingDurationSerializer
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from schools.models import School
from schools.school_mixin import SchoolMixin
from users.models import User


class TrainingDurationViewSet(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet
):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TrainingDurationSerializer

    def get_school(self):
        school_name = self.kwargs.get("school_name")
        return School.objects.get(name=school_name)

    def get_permissions(self, *args, **kwargs):
        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin", school=self.get_school()).exists():
            return permissions
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        student_id = serializer.validated_data.get("student")
        students_group_id = serializer.validated_data.get("students_group")

        try:
            student = User.objects.get(id=student_id)
            students_group = StudentsGroup.objects.get(
                group_id=students_group_id,
                students=student,
                course_id__school=self.get_school(),
            )
        except:
            return Response(
                f"В вашей школе такая группа с таким учеником не найдена.",
                status=status.HTTP_403_FORBIDDEN,
            )

        training_duration = TrainingDuration.objects.filter(
            user=student, students_group=students_group
        ).first()
        limit = serializer.validated_data.get("limit")
        if training_duration:
            if limit == 0:
                training_duration.delete()
            else:
                training_duration.limit = limit
                training_duration.save()
        else:
            if limit != 0:
                serializer.save()

        return HttpResponse("Продолжительность обучения установлена", status=201)
