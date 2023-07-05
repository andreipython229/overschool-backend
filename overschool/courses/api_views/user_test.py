from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import Answer, Question, SectionTest, UserTest
from courses.serializers import UserTestSerializer
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response


class UserTestViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    """Эндпоинт тестирования учеников\n
    <h2>/api/{school_name}/usertest/</h2>\n
    Тесты проходить могут только ученики\n
    Редактировать и удалять пройденные тесты могут только администраторы
    """

    queryset = UserTest.objects.all()
    serializer_class = UserTestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):

        user = self.request.user
        if not user.groups.filter(group__name="Student").exists():
            return Response(
                {"status": "Error", "message": "Тесты проходить могут только ученики"},
            )

        test = SectionTest.objects.get(pk=request.data.get("test"))
        user_attempts = UserTest.objects.filter(user=user, test=test)
        user_attempts_count = len(user_attempts)
        if test.attempt_count != 0 and user_attempts_count == test.attempt_count:
            return Response(
                {
                    "status": "Error",
                    "message": "Пользователь исчерпал лимит попыток для прохождения этого теста",
                },
            )
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
        if not user.groups.filter(group__name__in=["SuperAdmin", "Admin"]).exists():
            return Response(
                {
                    "status": "Error",
                    "message": "Редактировать пройденные тесты могут только администраторы",
                },
            )
        instance = self.get_object()
        user_test = UserTest.objects.get(pk=instance.pk)

        if request.data.get("status"):
            user_test.status = request.data.get("status")
        if request.data.get("success_percent"):
            user_test.success_percent = request.data.get("success_percent")

            serializer = self.serializer_class(user_test)

            return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):

        user = self.request.user
        if not user.groups.filter(group__name__in=["SuperAdmin", "Admin"]).exists():
            return Response(
                {
                    "status": "Error",
                    "message": "Удалять пройденные тесты могут только администраторы",
                },
            )

        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
