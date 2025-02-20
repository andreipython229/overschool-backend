from datetime import datetime, timedelta

from common_services.apply_swagger_auto_schema import apply_swagger_auto_schema
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, viewsets
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from schools.models import Bonus, School
from schools.school_mixin import SchoolMixin
from schools.serializers import BonusGetSerializer, BonusSerializer

s3 = UploadToS3()


@method_decorator(
    name="partial_update", decorator=swagger_auto_schema(tags=["school_bonuses"])
)
class BonusViewSet(WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet):
    """Эндпоинт получения, создания, изменения, удаления бонусов школы\n
    <h2>/api/{school_name}/school_bonuses/</h2>\n
    """

    http_method_names = ["get", "head", "post", "patch", "delete"]
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser,)

    def get_school(self):
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)
        return school

    def get_queryset(self, *args, **kwargs):
        if getattr(self, "swagger_fake_view", False):
            return (
                Bonus.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        user = self.request.user
        school = self.get_school()

        if user.groups.filter(group__name="Admin", school=school).exists():
            queryset = Bonus.objects.filter(school=school)
            search = self.request.GET.get("search")
            if search:
                tsquery = SearchQuery(search, config="russian")
                queryset = queryset.annotate(
                    search=SearchVector("text", config="russian")
                ).filter(search=tsquery)
            is_active = self.request.GET.get("is_active")
            if is_active:
                if is_active == "true":
                    queryset = queryset.filter(active=True)
                elif is_active == "false":
                    queryset = queryset.filter(active=False)
            if self.request.GET.get("start_date"):
                start_datetime = timezone.make_aware(
                    datetime.strptime(self.request.GET.get("start_date"), "%Y-%m-%d")
                )
                queryset = queryset.filter(expire_date__gte=start_datetime)

            if self.request.GET.get("end_date"):
                end_datetime = timezone.make_aware(
                    datetime.strptime(self.request.GET.get("end_date"), "%Y-%m-%d")
                    + timedelta(days=1)
                    - timedelta(seconds=1)
                )
                queryset = queryset.filter(expire_date__lte=end_datetime)

            return queryset
        if user.groups.filter(group__name="Student", school=school).exists():
            return Bonus.objects.filter(
                school=school, student_groups__students=user, active=True
            ).distinct()
        return Bonus.objects.none()

    def get_permissions(self, *args, **kwargs):
        school = self.get_school()
        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin", school=school).exists():
            return permissions
        elif self.action in ["list", "retrieve"] and (
            user.groups.filter(group__name="Student", school=school).exists()
            or user.email == "student@coursehub.ru"
        ):
            return permissions
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_serializer_class(self):
        if self.request.method == "GET":
            return BonusGetSerializer
        else:
            return BonusSerializer

    def create(self, request, *args, **kwargs):
        school = self.get_school()
        serializer = BonusSerializer(data=request.data, context={"view": self})
        serializer.is_valid(raise_exception=True)

        groups = serializer.validated_data.get("student_groups")
        if groups:
            school_groups = list(
                filter(lambda group: group.course_id.school == school, groups)
            )
            if len(groups) != len(school_groups):
                return Response(
                    {"error": "Не все указанные группы относятся к вашей школе"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if request.FILES.get("logo"):
            serializer.validated_data["logo"] = s3.upload_school_image(
                request.FILES["logo"], school.school_id
            )

        bonus = serializer.save(school=school, active=False)
        serializer = BonusGetSerializer(bonus)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = BonusSerializer(
            instance, data=request.data, context={"view": self}
        )
        serializer.is_valid(raise_exception=True)

        groups = serializer.validated_data.get("student_groups", [])
        school_groups = list(
            filter(lambda group: group.course_id.school == self.get_school(), groups)
        )

        if len(groups) != len(school_groups):
            return Response(
                {"error": "Не все указанные группы относятся к вашей школе"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.FILES.get("logo"):
            if instance.logo:
                s3.delete_file(str(instance.logo))
            serializer.validated_data["logo"] = s3.upload_school_image(
                request.FILES["logo"], instance.school.school_id
            )
        else:
            serializer.validated_data["logo"] = instance.logo

        self.perform_update(serializer)
        serializer = BonusGetSerializer(instance)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        remove_resp = ""
        if instance.logo:
            remove_resp = s3.delete_file(str(instance.logo))

        if remove_resp == "Error":
            return Response(
                {"error": "Ошибка удаления ресурса из хранилища Selectel"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)


BonusViewSet = apply_swagger_auto_schema(
    tags=["school_bonuses"], excluded_methods=["partial_update"]
)(BonusViewSet)
