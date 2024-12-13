from common_services.mixins import WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from schools.models import Box, BoxPrize, Prize, School
from schools.school_mixin import SchoolMixin
from schools.serializers import (
    BoxDetailSerializer,
    BoxPrizeSerializer,
    BoxSerializer,
    PrizeDetailSerializer,
    PrizeSerializer,
)

s3 = UploadToS3()


class BoxViewSet(WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet):
    serializer_class = BoxSerializer
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
        if self.action in [
            "list",
            "retrieve",
        ]:
            # Разрешения для просмотра курсов (любой пользователь школы)
            if (
                user.groups.filter(
                    group__name__in=["Student", "Teacher"], school=school_id
                ).exists()
                or user.email == "student@coursehub.ru"
            ):
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return BoxDetailSerializer
        return BoxSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Box.objects.none()  # Возвращаем пустой queryset при генерации схемы
        self.request.user
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
        return Box.objects.filter(school=school_id)

    def create(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        icon = (
            s3.upload_school_image(request.FILES["icon"], school_id)
            if request.FILES.get("icon")
            else None
        )
        box = serializer.save(icon=icon, school=School.objects.get(school_id=school_id))
        serializer = BoxDetailSerializer(box)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        box = self.get_object()
        school_id = box.school.school_id
        serializer = self.get_serializer(box, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if request.FILES.get("icon"):
            if box.icon:
                s3.delete_file(str(box.icon))
            serializer.validated_data["icon"] = s3.upload_school_image(
                request.FILES["icon"], school_id
            )
        else:
            serializer.validated_data["icon"] = box.icon
        self.perform_update(serializer)
        serializers = BoxDetailSerializer(box)

        return Response(serializers.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        box = self.get_object()
        self.perform_destroy(box)
        remove_resp = []
        if box.icon:
            remove_resp.append(s3.delete_file(str(box.icon)))

        if "Error" in remove_resp:
            return Response(
                {"error": "Ошибка удаления ресурса из хранилища Selectel"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)


class PrizeViewSet(WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet):
    serializer_class = PrizeSerializer
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
        if self.action in ["list", "retrieve"]:
            # Разрешения для просмотра призов (любой пользователь школы)
            if user.groups.filter(
                group__name__in=["Student", "Teacher"], school=school_id
            ).exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return PrizeDetailSerializer
        return PrizeSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return (
                Prize.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
        return Prize.objects.filter(school=school_id)

    def perform_active_check(self, prize):
        """
        Добавление/удаление приза в коробки в зависимости от статуса `is_active`.
        """
        if prize.is_active:
            # Если приз активный, добавляем его во все коробки
            boxes = Box.objects.filter(school=prize.school)
            for box in boxes:
                BoxPrize.objects.get_or_create(box=box, prize=prize)
        else:
            # Если приз неактивный, удаляем его из всех коробок
            BoxPrize.objects.filter(prize=prize).delete()

    def create(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Загружаем иконку в S3
        icon = (
            s3.upload_school_image(request.FILES["icon"], school_id)
            if request.FILES.get("icon")
            else None
        )

        # Создаем приз
        prize = serializer.save(
            icon=icon, school=School.objects.get(school_id=school_id)
        )

        # Проверяем активность и обновляем коробки
        self.perform_active_check(prize)

        serializer = PrizeDetailSerializer(prize)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        prize = self.get_object()
        school_id = prize.school.school_id

        serializer = self.get_serializer(prize, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Обновляем иконку в S3, если она передана
        if request.FILES.get("icon"):
            if prize.icon:
                s3.delete_file(str(prize.icon))
            serializer.validated_data["icon"] = s3.upload_school_image(
                request.FILES["icon"], school_id
            )

        # Обновляем объект
        self.perform_update(serializer)

        # Проверяем активность и обновляем коробки
        self.perform_active_check(prize)

        serializer = PrizeDetailSerializer(prize)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        prize = self.get_object()
        self.perform_destroy(prize)

        # Удаляем иконку из S3
        if prize.icon:
            s3.delete_file(str(prize.icon))

        return Response(status=status.HTTP_204_NO_CONTENT)
