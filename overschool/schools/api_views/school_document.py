from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from django.core.exceptions import PermissionDenied
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from schools.models import School, SchoolDocuments
from schools.school_mixin import SchoolMixin
from schools.serializers import (
    SchoolDocumentsDetailSerializer,
    SchoolDocumentsSerializer,
    SchoolDocumentsUpdateSerializer,
)

s3 = UploadToS3()


class SchoolDocumentViewSet(WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet):
    http_method_names = ["get", "head", "post", "patch", "delete"]
    permission_classes = [permissions.IsAuthenticated]

    def get_school(self):
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)
        return school

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return (
                SchoolDocuments.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы

        return SchoolDocuments.objects.filter(school=self.get_school())

    def get_permissions(self, *args, **kwargs):
        school = self.get_school()
        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user == school.owner:
            return permissions
        print(
            user.groups.filter(group__name="Admin", school=school).exists(), self.action
        )
        if user.groups.filter(
            group__name="Admin", school=school
        ).exists() and self.action in ["list", "retrieve", "partial_update"]:
            return permissions
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_serializer_class(self):
        if self.request.method == "GET":
            return SchoolDocumentsDetailSerializer
        if self.request.method == "PATCH":
            return SchoolDocumentsUpdateSerializer
        return SchoolDocumentsSerializer

    def create(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        user = self.request.user
        school_id = self.request.data.get("school")
        school = School.objects.get(name=school_name)
        if school.school_id != school_id or school.owner != user:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

        serializer = SchoolDocumentsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        school_document = serializer.save(user=user)

        if request.FILES.get("stamp"):
            stamp = s3.upload_school_image(request.FILES["stamp"], school)
            school_document.stamp = stamp
            school_document.save()
        if request.FILES.get("signature"):
            signature = s3.upload_school_image(request.FILES["signature"], school)
            school_document.signature = signature
            school_document.save()

        serializer = SchoolDocumentsSerializer(school_document)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        print("k")
        instance = self.get_object()
        serializer = SchoolDocumentsUpdateSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.FILES.get("stamp"):
            if instance.stamp:
                s3.delete_file(str(instance.stamp))
            serializer.validated_data["stamp"] = s3.upload_school_image(
                request.FILES["stamp"], instance.school_id
            )
        else:
            serializer.validated_data["stamp"] = instance.stamp

        if request.FILES.get("signature"):
            if instance.signature:
                s3.delete_file(str(instance.signature))
            serializer.validated_data["signature"] = s3.upload_school_image(
                request.FILES["signature"], instance.school_id
            )
        else:
            serializer.validated_data["signature"] = instance.signature

        self.perform_update(serializer)
        serializer = SchoolDocumentsDetailSerializer(instance)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        remove_resp = []
        if instance.stamp:
            remove_resp.append(s3.delete_file(str(instance.stamp)))
        if instance.signature:
            remove_resp.append(s3.delete_file(str(instance.signature)))

        if "Error" in remove_resp:
            return Response(
                {"error": "Ошибка удаления ресурса из хранилища Selectel"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)
