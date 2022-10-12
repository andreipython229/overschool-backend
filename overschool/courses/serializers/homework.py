from courses.models import Homework
from rest_framework import serializers


class HomeworkSerializer(serializers.ModelSerializer):
    """
    Сериализатор моедли домашнего задания
    """

    type = serializers.CharField(default="homework")

    class Meta:
        model = Homework
        fields = [
            "lesson_id",
            "section",
            "name",
            "order",
            "author_id",
            "description",
            "automate_accept",
            "time_accept",
            "points",
            "type",
        ]
