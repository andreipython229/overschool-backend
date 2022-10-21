from rest_framework import serializers

from courses.models import StudentsTableInfo


class StudentsTableInfoSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели отображения информации о студентах в таблице у админа
    """

    class Meta:
        model = StudentsTableInfo
        fields = "__all__"
