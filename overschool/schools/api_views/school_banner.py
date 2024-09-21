from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models.students.students_group import StudentsGroup
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from schools.models import Banner, BannerAccept, BannerClick, School
from schools.school_mixin import SchoolMixin
from schools.serializers import (
    BannerAcceptSerializer,
    BannerClickSerializer,
    BannerSerializer,
)


class BannerViewSet(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet
):

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BannerSerializer

    def get_permissions(self, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return permissions
        if self.action in [
            "list",
            "retrieve",
            "accept",
        ]:
            if user.groups.filter(group__name="Student", school=school_id).exists() or user.email == "student@coursehub.ru":
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_queryset(self, *args, **kwargs):
        if getattr(self, "swagger_fake_view", False):
            return (
                Banner.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
        user = self.request.user
        if user.groups.filter(
            group__name__in=["Student", "Teacher"], school=school_id
        ).exists():
            return Banner.objects.filter(school=school_id, is_active=True)
        return Banner.objects.filter(school=school_id)

    def list(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
        queryset = self.get_queryset()
        user = request.user
        if user.groups.filter(group__name="Student", school=school_id).exists():
            if user.groups.filter(group__name="Student").exists():
                user_groups = user.students_group_fk.all()
                if not user_groups.exists():
                    return Response(Banner.objects.none())

                # Фильтруем баннеры по группам пользователя и активным
                queryset = queryset.filter(
                    is_active=True, groups__in=user_groups
                ).distinct()
                if queryset.exists():
                    # Возвращаем только один активный баннер
                    banner = queryset.first()
                    BannerClick.objects.create(banner=banner, user=user)
                    serializer = self.get_serializer(banner)
                    return Response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user

        # Проверка на принадлежность к администратору школы
        if user.groups.filter(group__name="Admin", school=instance.school).exists():
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        # Проверка на принадлежность пользователя к группам, указанным в баннере
        user_groups = user.students_group_fk.filter(
            group_id__in=instance.groups.values_list("group_id", flat=True)
        )
        if not user_groups.exists():
            return Response(Banner.objects.none())

        # Запись клика и возврат данных баннера
        BannerClick.objects.create(banner=instance, user=user)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)

        # Деактивируем другие баннеры, если создается новый активный баннер
        if serializer.validated_data.get("is_active"):
            Banner.objects.filter(school=school, is_active=True).update(is_active=False)

        # Устанавливаем группы по умолчанию, если они не указаны
        if not serializer.validated_data.get("groups"):
            groups = StudentsGroup.objects.filter(course_id__school=school)
            serializer.save(school=school, groups=groups)
        else:
            serializer.save(school=school)

    def perform_update(self, serializer, *args, **kwargs):
        if serializer.validated_data.get("is_active"):
            school_name = self.kwargs.get("school_name")
            school = School.objects.get(name=school_name)
            Banner.objects.filter(school=school, is_active=True).update(is_active=False)
        serializer.save()

    @action(
        detail=True, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def statistics(self, request, pk=None, *args, **kwargs):
        banner = self.get_object()
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        clicks = BannerClick.objects.filter(banner=banner)
        if start_date:
            clicks = clicks.filter(timestamp__gte=start_date)
        if end_date:
            clicks = clicks.filter(timestamp__lte=end_date)

        total_clicks = clicks.count()
        unique_clicks = clicks.values("user").distinct().count()

        click_details = clicks.select_related("user").values("timestamp", "user__email")

        return Response(
            {
                "total_clicks": total_clicks,
                "unique_clicks": unique_clicks,
                "click_details": list(click_details),
            }
        )

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def accept(self, request, pk=None, *args, **kwargs):
        banner = self.get_object()
        user = request.user
        accept, created = BannerAccept.objects.get_or_create(banner=banner, user=user)
        accept.is_accepted = True
        accept.save()
        return Response({"status": "accepted"})
