from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.yandex_client import remove_from_yandex, upload_file
from courses.models import BaseLesson, Question, SectionTest
from courses.serializers import QuestionGetSerializer, QuestionSerializer
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response


class QuestionViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    """Эндпоинт на получение, создания, изменения и удаления вопросов \n
    Получать курсы может любой пользователь. \n
    Создавать, изменять, удалять - пользователь с правами группы Admin."""

    queryset = Question.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve", "update", "partial_update"]:
            return QuestionGetSerializer
        else:
            return QuestionSerializer

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action in ["list", "retrieve"]:
            # Разрешения для просмотра вопросов (любой пользователь)
            return permissions
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            # Разрешения для создания и изменения вопросов (только пользователи с группой 'Admin')
            user = self.request.user
            if user.groups.filter(group__name="Admin").exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            return permissions

    def create(self, request, *args, **kwargs):
        serializer = QuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.FILES.get("picture"):
            test = SectionTest.objects.get(pk=request.data["test"])
            base_lesson = BaseLesson.objects.get(tests=test)
            serializer.validated_data["picture"] = upload_file(
                request.FILES["picture"], base_lesson
            )

        question = serializer.save()
        serializer = QuestionGetSerializer(question)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = QuestionGetSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.FILES.get("picture"):
            if instance.picture:
                remove_from_yandex(str(instance.picture))
            base_lesson = BaseLesson.objects.get(tests=instance.test)
            serializer.validated_data["picture"] = upload_file(
                request.FILES["picture"], base_lesson
            )
        else:
            serializer.validated_data["picture"] = instance.picture

        self.perform_update(serializer)
        serializer = QuestionGetSerializer(instance)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        remove_resp = None
        if instance.picture:
            if remove_from_yandex(str(instance.picture)) == "Error":
                remove_resp = "Error"
        for file_obj in list(instance.answers.exclude(picture="").values("picture")):
            if remove_from_yandex(str(file_obj["picture"])) == "Error":
                remove_resp = "Error"

        self.perform_destroy(instance)

        if remove_resp == "Error":
            return Response(
                {"error": "Запрашиваемый путь на диске не существует"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)
