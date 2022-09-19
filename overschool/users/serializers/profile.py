from rest_framework import serializers
from users.models import Profile, User


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для личного кабинета пользователя"""

    class Meta:
        model = User
        fields = ["id", "email", "phone_number", "first_name", "last_name"]


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для личного кабинета пользователя"""
    user = UserSerializer()

    class Meta:
        model = Profile
        fields = ["profile_id", "avatar", "avatar_url", "city", "sex", "description", "user"]

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user")

        if user_data:
            user = instance.user
            user.first_name = user_data.get("first_name", user.first_name)
            user.last_name = user_data.get("last_name", user.last_name)
            user.email = user_data.get("email", user.email)
            user.phone_number = user_data.get("phone_number", user.phone_number)

            user.save()

            return super().update(instance=instance, validated_data=validated_data)
