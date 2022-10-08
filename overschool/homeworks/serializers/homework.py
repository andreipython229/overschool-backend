from rest_framework import serializers

from homeworks.models import Homework


class HomeworkSerializer(serializers.ModelSerializer):
    """
    Сериализатор моедли домашнего задания
    """
    type = serializers.CharField(default="homework")
    class Meta:
        model = Homework
        fields = [
            "homework_id",
            "section",
            "name",
            "text",
            "file",
            "type"
            "order"
        ]
