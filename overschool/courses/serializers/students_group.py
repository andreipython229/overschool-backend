from rest_framework import serializers

from courses.models import StudentsGroup


class StudentsGroupSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели группы студентов
    """

    class Meta:
        model = StudentsGroup
        fields = "__all__"


class GroupStudentsSerializer(serializers.Serializer):
    """
    Сериализатор
    """
    group_id = serializers.IntegerField(help_text="Номер группы")

    class Meta:
        fields = '__all__'