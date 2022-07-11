from rest_framework import serializers

from lms_User.models import Homework



class HomeworkSerializer(serializers.ModelSerializer):
    """
    Сериализатор моедли домашнего задания
    """

    class Meta:
        model = Homework
        fields = '__all__'

