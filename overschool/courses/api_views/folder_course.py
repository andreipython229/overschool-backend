from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import Folder
from courses.serializers import FolderCourseSerializer, FolderViewSerializer
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from schools.models import School
from schools.school_mixin import SchoolMixin


class FolderCourseViewSet(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet
):
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return permissions
        if user.groups.filter(
            group__name__in=["Student", "Teacher"], school=school_id
        ).exists() and self.action in ["list", "retrieve"]:
            return permissions
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return (
                Folder.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        user = self.request.user
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        if user.groups.filter(
            group__name__in=["Student", "Teacher", "Admin"], school=school_id
        ).exists():
            return Folder.objects.filter(school__name=school_name)
        return Folder.objects.none()

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return FolderViewSerializer
        else:
            return FolderCourseSerializer

    def create(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(school=school)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        self.perform_destroy(instance)

        return Response(status=status.HTTP_204_NO_CONTENT)
