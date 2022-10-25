from rest_framework import serializers

from courses.models import Homework


class HomeworkSerializer(serializers.ModelSerializer):
    """
    Сериализатор моедли домашнего задания
    """

    type = serializers.CharField(default="homework", read_only=True)

    class Meta:
        model = Homework
        fields = [
            "homework_id",
            "section",
            "name",
            "order",
            "author_id",
            "description",
            "automate_accept",
            "time_accept",
            "points",
            "type"
        ]
        read_only_fields = ["type"]
