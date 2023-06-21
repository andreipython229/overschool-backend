from common_services.yandex_client import get_yandex_link
from courses.models import Question
from rest_framework import serializers


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
        return get_yandex_link(str(obj.picture))
