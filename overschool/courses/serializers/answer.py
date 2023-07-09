from common_services.selectel_client import SelectelClient
from courses.models import Answer
from rest_framework import serializers

s = SelectelClient()


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
        return s.get_selectel_link(str(obj.picture)) if obj.picture else None
