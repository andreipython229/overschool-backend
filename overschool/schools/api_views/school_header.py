from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.yandex_client import remove_from_yandex, upload_school_image
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from schools.models import SchoolHeader
from schools.serializers import SchoolHeaderDetailSerializer, SchoolHeaderSerializer


class SchoolHeaderViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    """Эндпоинт на получение, создания, изменения и удаления хедера школы.\n
    <h2>/api/{school_name}/school_header/</h2>\n
    Эндпоинт на получение, создания, изменения и удаления хедера школы
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin").exists():
            return permissions
        if self.action in ["list", "retrieve"]:
            # Разрешения для просмотра домашних заданий (любой пользователь школы)
            if user.groups.filter(group__name__in=["Teacher", "Student"]).exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        queryset = SchoolHeader.objects.filter(school__groups__user=user)
        return queryset

    def get_serializer_class(self):
        if self.action in ["retrieve", "update"]:
            return SchoolHeaderDetailSerializer
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
        serializer = SchoolHeaderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        logo_school = (
            upload_school_image(request.FILES["logo_school"], school)
            if request.FILES.get("logo_school")
            else None
        )
        logo_header = (
            upload_school_image(request.FILES["logo_header"], school)
            if request.FILES.get("logo_header")
            else None
        )
        photo_background = (
            upload_school_image(request.FILES["photo_background"], school)
            if request.FILES.get("photo_background")
            else None
        )
        favicon = (
            upload_school_image(request.FILES["favicon"], school)
            if request.FILES.get("favicon")
            else None
        )
        serializer.save(
            logo_school=logo_school,
            logo_header=logo_header,
            photo_background=photo_background,
            favicon=favicon,
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        school_header = self.get_object()
        user = self.request.user
        school_id = school_header.school.school_id
        if not user.groups.filter(
            group__name="Admin", school=school_header.school
        ).exists():
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

        if request.FILES.get("logo_school"):
            if school_header.logo_school:
                remove_from_yandex(str(school_header.logo_school))
            school_header.logo_school = upload_school_image(
                request.FILES["logo_school"], school_id
            )
        if request.FILES.get("logo_header"):
            if school_header.logo_header:
                remove_from_yandex(str(school_header.logo_header))
            school_header.logo_header = upload_school_image(
                request.FILES["logo_header"], school_id
            )
        if request.FILES.get("photo_background"):
            if school_header.photo_background:
                remove_from_yandex(str(school_header.photo_background))
            school_header.photo_background = upload_school_image(
                request.FILES["photo_background"], school_id
            )
        if request.FILES.get("favicon"):
            if school_header.favicon:
                remove_from_yandex(str(school_header.favicon))
            school_header.favicon = upload_school_image(
                request.FILES["favicon"], school_id
            )
        school_header.description = request.data.get(
            "description", school_header.description
        )
        school_header.name = request.data.get("name", school_header.name)
        school_header.save()
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
            remove_resp.append(remove_from_yandex(str(instance.logo_school)))
        if instance.logo_header:
            remove_resp.append(remove_from_yandex(str(instance.logo_header)))
        if instance.photo_background:
            remove_resp.append(remove_from_yandex(str(instance.photo_background)))
        if instance.favicon:
            remove_resp.append(remove_from_yandex(str(instance.favicon)))

        if "Error" in remove_resp:
            return Response(
                {"error": "Запрашиваемый путь на диске не существует"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)
