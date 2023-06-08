from common_services.yandex_client import get_yandex_link
from courses.models import Answer
from rest_framework import serializers


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
        return get_yandex_link(str(obj.picture))
