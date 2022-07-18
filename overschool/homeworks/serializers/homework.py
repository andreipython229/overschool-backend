from homeworks.models import Homework
from rest_framework import serializers


class HomeworkSerializer(serializers.ModelSerializer):
    """
    Сериализатор моедли домашнего задания
    """

    class Meta:
        model = Homework
        fields = "__all__"
