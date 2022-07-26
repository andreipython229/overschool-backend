from rest_framework import serializers
from users.models import Profile

from .user import UserInitialsSerializer


class ProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для личного кабинета пользователя"""

    user = UserInitialsSerializer()

    class Meta:
        model = Profile
        fields = (
            "user",
            "avatar",
            "phone_number",
            "city",
            "description",
            "sex",
        )

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user")

        if user_data:
            user = instance.user
            user.first_name = user_data.get("first_name", user.first_name)
            user.last_name = user_data.get("last_name", user.last_name)
            user.email = user_data.get("email", user.email)

            user.save()

        return super().update(instance=instance, validated_data=validated_data)
