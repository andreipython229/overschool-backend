from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.yandex_client import remove_from_yandex, upload_file
from courses.models import Answer, BaseLesson, Question
from courses.serializers import AnswerGetSerializer, AnswerSerializer
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response


class AnswerViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    """Эндпоинт на получение, создания, изменения и удаления уроков.\n
    <h2>/api/{school_name}/answers/</h2>\n
    Разрешения для просмотра ответов к тестам (любой пользователь).\n
    Разрешения для создания и изменения ответов к тестам (только пользователи с группой 'Admin').
    """

    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return AnswerGetSerializer
        else:
            return AnswerSerializer

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action in ["list", "retrieve"]:
            # Разрешения для просмотра ответов к тестам (любой пользователь)
            return permissions
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            # Разрешения для создания и изменения ответов к тестам (только пользователи с группой 'Admin')
            user = self.request.user
            if user.groups.filter(group__name="Admin").exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            return permissions

    def create(self, request, *args, **kwargs):
        serializer = AnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.FILES.get("picture"):
            question = Question.objects.get(pk=request.data["question"])
            base_lesson = BaseLesson.objects.get(tests=question.test)
            serializer.validated_data["picture"] = upload_file(
                request.FILES["picture"], base_lesson
            )

        answer = serializer.save()
        serializer = AnswerGetSerializer(answer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = AnswerSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.FILES.get("picture"):
            if instance.picture:
                remove_from_yandex(str(instance.picture))
            base_lesson = BaseLesson.objects.get(tests=instance.question.test)
            serializer.validated_data["picture"] = upload_file(
                request.FILES["picture"], base_lesson
            )
        else:
            serializer.validated_data["picture"] = instance.picture

        self.perform_update(serializer)
        serializer = AnswerGetSerializer(instance)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)

        remove_resp = (
            remove_from_yandex(str(instance.picture)) if instance.picture else None
        )
        if remove_resp == "Error":
            return Response(
                {"error": "Запрашиваемый путь на диске не существует"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)
