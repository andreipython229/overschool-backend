from rest_framework import serializers

from homeworks.models import Homework


class HomeworkSerializer(serializers.ModelSerializer):
    """
    Сериализатор моедли домашнего задания
    """

    class Meta:
        model = Homework
        fields = ["homework_id",
                  "section",
                  "name",
                  "order",
                  "author_id",
                  "text",
                  "file",
                  "file_url",
                  "published",
                  "automate_accept",
                  "time_accept",
                  "balls", ]
