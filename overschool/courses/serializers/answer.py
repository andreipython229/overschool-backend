from common_services.selectel_client import UploadToS3
from courses.models import Answer
from rest_framework import serializers

s3 = UploadToS3()


class AnswerSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели ответа
    """

    class Meta:
        model = Answer
        fields = "__all__"


class AnswerGetSerializer(serializers.ModelSerializer):
    """
    Сериализатор просмотра ответа
    """

    picture = serializers.SerializerMethodField()

    class Meta:
        model = Answer
        fields = "__all__"

    def get_picture(self, obj):
        return s3.get_link(obj.picture.name) if obj.picture else None


class AnswerListGetSerializer(serializers.ModelSerializer):
    """
    Сериализатор для просмотра списка ответов
    """

    picture = serializers.SerializerMethodField()

    class Meta:
        model = Answer
        fields = (
            "answer_id",
            "body",
            "is_correct",
            "question",
            "picture",
            "answer_in_range",
            "from_digit",
            "to_digit",
        )

    def get_picture(self, obj):
        return s3.get_link(obj.picture.name) if obj.picture else None
