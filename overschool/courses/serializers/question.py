from common_services.selectel_client import UploadToS3
from courses.models import Answer, Question
from courses.serializers import AnswerListGetSerializer
from rest_framework import serializers

s3 = UploadToS3()


class QuestionSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели вопроса
    """

    class Meta:
        model = Question
        fields = "__all__"


class QuestionGetSerializer(serializers.ModelSerializer):
    """
    Сериализатор просмотра вопроса
    """

    picture = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = "__all__"
        read_only_fields = ("test",)

    def get_picture(self, obj):
        return s3.get_link(obj.picture.name) if obj.picture else None


class QuestionListGetSerializer(serializers.ModelSerializer):
    """
    Сериализатор для просмотра списка вопросов
    """

    picture = serializers.SerializerMethodField()
    answers = AnswerListGetSerializer(Answer, many=True)

    class Meta:
        model = Question
        fields = (
            "question_id",
            "question_type",
            "multiple_answer",
            "body",
            "picture",
            "answers",
        )

    def get_picture(self, obj):
        return s3.get_link(obj.picture.name) if obj.picture else None
