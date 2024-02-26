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


class SchoolDocumentViewSet(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet
):
    http_method_names = ["get", "head", "post", "patch", "delete"]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return (
                SchoolDocuments.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        user = self.request.user
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        return SchoolDocuments.objects.filter(user=user, school=school_id)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return SchoolDocumentsDetailSerializer
        if self.request.method == "PATCH":
            return SchoolDocumentsUpdateSerializer
        return SchoolDocumentsSerializer

    def create(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        user = self.request.user
        owner = self.request.data.get("user")
        school = self.request.data.get("school")
        school_id = School.objects.get(name=school_name)
        if (
            school_id.school_id != school
            or school_id.owner != owner
            and school_id.owner != user
        ):
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

        serializer = SchoolDocumentsSerializer(data={**request.data})
        serializer.is_valid(raise_exception=True)
        school_document = serializer.save()

        if request.FILES.get("stamp"):
            stamp = s3.upload_school_image(request.FILES["photo_background"], school)
            school_document.stamp = stamp
            school_document.save()
        if request.FILES.get("signature"):
            signature = s3.upload_school_image(request.FILES["signature"], school)
            school_document.signature = signature
            school_document.save()

        serializer = SchoolDocumentsSerializer(school_document)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):

        instance = self.get_object()
        user = self.request.user
        if instance.user != user:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        serializer = SchoolDocumentsUpdateSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.FILES.get("stamp"):
            if instance.logo_school:
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
        user = self.request.user
        if instance.user != user:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
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
