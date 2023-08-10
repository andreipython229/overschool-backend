from common_services.apply_swagger_auto_schema import apply_swagger_auto_schema
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import SelectelClient
from courses.models import BaseLesson, Question, SectionTest
from courses.serializers import QuestionGetSerializer, QuestionSerializer
from django.utils.decorators import method_decorator
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .schemas.question import QuestionsSchemas

s = SelectelClient()


@method_decorator(
    name="update",
    decorator=QuestionsSchemas.question_update_schema(),
)
@method_decorator(
    name="partial_update",
    decorator=QuestionsSchemas.question_update_schema(),
)
class QuestionViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    """Эндпоинт на получение, создания, изменения и удаления вопросов \n
    <h2>/api/{school_name}/questions/</h2>\n
    Получать вопросы может любой пользователь. \n
    Создавать, изменять, удалять - пользователь с правами группы Admin."""

    queryset = Question.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    # parser_classes = (MultiPartParser,)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
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
            serializer.validated_data["picture"] = s.upload_file(
                request.FILES["picture"], base_lesson
            )

        question = serializer.save()
        serializer = QuestionGetSerializer(question)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = QuestionSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.FILES.get("picture"):
            if instance.picture:
                s.remove_from_selectel(str(instance.picture))
            base_lesson = BaseLesson.objects.get(tests=instance.test)
            serializer.validated_data["picture"] = s.upload_file(
                request.FILES["picture"], base_lesson
            )
        else:
            serializer.validated_data["picture"] = instance.picture

        self.perform_update(serializer)
        serializer = QuestionGetSerializer(instance)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        files_to_delete = []
        if instance.picture:
            files_to_delete.append(str(instance.picture))
        for file_obj in list(instance.answers.exclude(picture="").values("picture")):
            files_to_delete.append(str(file_obj["picture"]))

        remove_resp = (
            s.bulk_remove_from_selectel(files_to_delete) if files_to_delete else None
        )

        self.perform_destroy(instance)

        if remove_resp == "Error":
            return Response(
                {"error": "Ошибка удаления ресурса из хранилища Selectel"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)


QuestionViewSet = apply_swagger_auto_schema(
    default_schema=QuestionsSchemas.default_schema(),
    excluded_methods=["update", "partial_update"],
)(QuestionViewSet)
