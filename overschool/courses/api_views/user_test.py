from common_services.apply_swagger_auto_schema import apply_swagger_auto_schema
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import Answer, Question, SectionTest, UserTest
from courses.serializers import UserTestSerializer
from django.core.exceptions import PermissionDenied
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from schools.models import School
from schools.school_mixin import SchoolMixin


class UserTestViewSet(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet
):
    """Эндпоинт тестирования учеников\n
    <h2>/api/{school_name}/usertest/</h2>\n
    Тесты проходить могут только ученики\n
    Редактировать и удалять пройденные тесты могут только администраторы
    """

    serializer_class = UserTestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if (
            user.groups.filter(
                group__name__in=["Student", "Admin"], school=school_id
            ).exists()
            or user.email == "student@coursehub.ru"
        ):
            return permissions
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_queryset(self, *args, **kwargs):
        if getattr(self, "swagger_fake_view", False):
            return (
                UserTest.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
        user = self.request.user

        if user.groups.filter(group__name="Student", school=school_id).exists():
            return UserTest.objects.filter(
                user=user, test__section__course__school__name=school_name
            ).order_by("-created_at")
        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return UserTest.objects.filter(
                test__section__course__school__name=school_name
            ).order_by("-created_at")
        return UserTest.objects.none()

    def create(self, request, *args, **kwargs):
        user = self.request.user
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
        if not user.groups.filter(group__name="Student", school=school_id).exists():
            return Response(
                {"status": "Error", "message": "Тесты проходить могут только ученики"},
            )

        test = SectionTest.objects.get(pk=request.data.get("test"))
        if UserTest.objects.filter(user=user, test=test, status=True).exists():
            return Response(
                {
                    "status": "Error",
                    "message": "Этот тест уже пройден пользователем",
                },
            )

        # Находим самый последний (по created_at) объект UserTest для данного пользователя и теста
        user_test = (
            UserTest.objects.filter(user=user, test=test)
            .order_by("-created_at")
            .first()
        )

        # Если объект UserTest найден, обновляем его статус
        if user_test:
            test_status = (
                True
                if int(request.data.get("success_percent")) >= test.success_percent
                else False
            )
            user_test.status = test_status
            user_test.success_percent = request.data.get("success_percent")
            user_test.save()

            # Возвращаем обновленный объект UserTest
            serializer = self.serializer_class(user_test)
            return Response(serializer.data, status=status.HTTP_200_OK)

            # Если объект UserTest не найден, возвращаем ошибку
        else:
            serializer = self.serializer_class(data=request.data)

            if serializer.is_valid():
                test_status = (
                    True
                    if int(request.data.get("success_percent")) >= test.success_percent
                    else False
                )
                serializer.save(user=user, status=test_status)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(
                {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        user = self.request.user
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
        if not user.groups.filter(group__name="Admin", school=school_id).exists():
            return Response(
                {
                    "status": "Error",
                    "message": "Редактировать пройденные тесты могут только администраторы",
                },
            )
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        user = self.request.user
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
        if not user.groups.filter(group__name="Admin", school=school_id).exists():
            return Response(
                {
                    "status": "Error",
                    "message": "Удалять пройденные тесты могут только администраторы",
                },
            )

        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


UserTestViewSet = apply_swagger_auto_schema(
    tags=[
        "user_test",
    ]
)(UserTestViewSet)
