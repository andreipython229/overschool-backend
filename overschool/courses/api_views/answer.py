from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import SelectelClient
from courses.models import Answer, BaseLesson, Question
from courses.serializers import AnswerGetSerializer, AnswerSerializer
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .schemas.answer import answer_schema
from .schemas.apply_auto_schema import apply_swagger_auto_schema

s = SelectelClient()


class AnswerViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    """Эндпоинт на получение, создания, изменения и удаления уроков.\n
    <h2>/api/{school_name}/answers/</h2>\n
    Разрешения для просмотра ответов к тестам (любой пользователь).\n
    Разрешения для создания и изменения ответов к тестам (только пользователи с группой 'Admin').
    """

    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser,)

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
            serializer.validated_data["picture"] = s.upload_file(
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
                s.remove_from_selectel(str(instance.picture))
            base_lesson = BaseLesson.objects.get(tests=instance.question.test)
            serializer.validated_data["picture"] = s.upload_file(
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
            s.remove_from_selectel(str(instance.picture)) if instance.picture else None
        )
        if remove_resp == "Error":
            return Response(
                {"error": "Ошибка удаления ресурса из хранилища Selectel"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)


AnswerViewSet = apply_swagger_auto_schema(answer_schema)(AnswerViewSet)
