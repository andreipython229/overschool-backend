from common_services.apply_swagger_auto_schema import apply_swagger_auto_schema
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from django.utils.decorators import method_decorator
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from schools.models import SchoolHeader
from schools.serializers import (
    SchoolHeaderDetailSerializer,
    SchoolHeaderSerializer,
    SchoolHeaderUpdateSerializer,
)

from .schemas.school_header import SchoolHeaderSchemas

s3 = UploadToS3()


@method_decorator(
    name="partial_update",
    decorator=SchoolHeaderSchemas.partial_update_schema(),
)
class SchoolHeaderViewSet(WithHeadersViewSet, viewsets.ModelViewSet):
    """Эндпоинт на получение, создания, изменения и удаления хедера школы.\n
    <h2>/api/{school_name}/school_header/</h2>\n
    Эндпоинт на получение, создания, изменения и удаления хедера школы
    """

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser,)

    def get_permissions(self):

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin").exists():
            return permissions
        if self.action in ["list", "retrieve"]:
            if (
                user.groups.filter(group__name__in=["Teacher", "Student"]).exists()
                or user.email == "student@coursehub.ru"
            ):
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_queryset(self, *args, **kwargs):
        if getattr(self, "swagger_fake_view", False):
            return (
                SchoolHeader.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        user = self.request.user
        queryset = SchoolHeader.objects.filter(school__groups__user=user)
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SchoolHeaderDetailSerializer
        elif self.action == "update":
            return SchoolHeaderUpdateSerializer
        else:
            return SchoolHeaderSerializer

    def create(self, request, *args, **kwargs):
        user = self.request.user
        if not user.groups.filter(group__name="Admin").exists():
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        school = self.request.data.get("school")
        if school is not None:
            if not user.groups.filter(group__name="Admin", school=school).exists():
                raise PermissionDenied("Вы не являетесь администратором данной школы.")

        # Проверяем, существует ли уже шапка для указанной школы
        existing_header = SchoolHeader.objects.filter(school=school).first()
        if existing_header:
            raise ValidationError("Для данной школы уже существует шапка.")

        serializer = SchoolHeaderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        school_id = request.data.get("school")

        logo_school = (
            s3.upload_school_image(request.FILES["logo_school"], school_id)
            if request.FILES.get("logo_school")
            else None
        )
        photo_background = (
            s3.upload_school_image(request.FILES["photo_background"], school_id)
            if request.FILES.get("photo_background")
            else None
        )
        school_header = serializer.save(
            logo_school=logo_school,
            photo_background=photo_background,
        )
        serializer = SchoolHeaderDetailSerializer(school_header)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        school_header = self.get_object()
        user = self.request.user
        school_id = school_header.school.school_id
        if not user.groups.filter(
            group__name="Admin", school=school_header.school
        ).exists():
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

        serializer = SchoolHeaderUpdateSerializer(school_header, data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.FILES.get("logo_school"):
            if school_header.logo_school:
                s3.delete_file(str(school_header.logo_school))
            serializer.validated_data["logo_school"] = s3.upload_school_image(
                request.FILES["logo_school"], school_id
            )
        else:
            serializer.validated_data["logo_school"] = school_header.logo_school

        if request.FILES.get("photo_background"):
            if school_header.photo_background:
                s3.delete_file(str(school_header.photo_background))
            serializer.validated_data["photo_background"] = s3.upload_school_image(
                request.FILES["photo_background"], school_id
            )
        else:
            serializer.validated_data[
                "photo_background"
            ] = school_header.photo_background

        self.perform_update(serializer)
        serializer = SchoolHeaderDetailSerializer(school_header)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = self.request.user
        if not user.groups.filter(group__name="Admin", school=instance.school).exists():
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        self.perform_destroy(instance)
        remove_resp = []
        if instance.logo_school:
            remove_resp.append(s3.delete_file(str(instance.logo_school)))
        if instance.photo_background:
            remove_resp.append(s3.delete_file(str(instance.photo_background)))

        if "Error" in remove_resp:
            return Response(
                {"error": "Ошибка удаления ресурса из хранилища Selectel"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)


SchoolHeaderViewSet = apply_swagger_auto_schema(
    tags=["school_header"],
    excluded_methods=[
        "partial_update",
    ],
)(SchoolHeaderViewSet)
