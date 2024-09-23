from rest_framework import serializers
from schools.models import SchoolNewRole


class SchoolNewRoleSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели новых ролей для пользователей школы
    """

    class Meta:
        model = SchoolNewRole
        fields = "__all__"
