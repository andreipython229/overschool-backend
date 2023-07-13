from common_services.selectel_client import SelectelClient
from courses.models import Question
from rest_framework import serializers

s = SelectelClient()


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
        return s.get_selectel_link(str(obj.picture)) if obj.picture else None
