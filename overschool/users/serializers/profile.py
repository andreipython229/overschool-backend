from rest_framework import serializers
from users.models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для личного кабинета пользователя"""

    email = serializers.CharField(source="user.email")
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")

    class Meta:
        model = Profile
        fields = (
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "city",
            "description",
            "sex",
        )
