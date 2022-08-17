from rest_framework import serializers

from courses.models import StudentsGroup


class StudentsGroupSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели группы студентов
    """

    class Meta:
        model = StudentsGroup
        fields = "__all__"