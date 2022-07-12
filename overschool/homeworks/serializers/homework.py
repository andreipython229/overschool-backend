from rest_framework import serializers

from homeworks.models import Homework


class HomeworkSerializer(serializers.ModelSerializer):
    """
    Сериализатор моедли домашнего задания
    """

    class Meta:
        model = Homework
        fields = "__all__"
