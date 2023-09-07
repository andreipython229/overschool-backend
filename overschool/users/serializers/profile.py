from common_services.selectel_client import SelectelClient
from rest_framework import serializers
from users.models import Profile, User

s = SelectelClient()


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для изменения профиля в личном кабинете пользователя"""

    user = ProfileSerializer()

    class Meta:
        model = Profile
        fields = [
            "profile_id",
            "avatar",
            "avatar_url",
            "city",
            "sex",
            "description",
            "user",
        ]

    def update(self, instance, validated_data):
        if "user" in validated_data:
            user_data = validated_data.pop("user")

            user = instance.user
            user.first_name = user_data.get("first_name", user.first_name)
            user.last_name = user_data.get("last_name", user.last_name)
            user.email = user_data.get("email", user.email)
            user.phone_number = user_data.get("phone_number", user.phone_number)

            user.save()

            return super().update(instance=instance, validated_data=validated_data)

        instance.avatar = validated_data.get("avatar", instance.avatar)
        instance.city = validated_data.get("city", instance.city)
        instance.sex = validated_data.get("sex", instance.sex)
        instance.description = validated_data.get("description", instance.description)

        instance.save()

        return instance


class UserProfileGetSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра профиля пользователя"""

    user = ProfileSerializer()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            "profile_id",
            "avatar",
            "avatar_url",
            "city",
            "sex",
            "description",
            "user",
        ]

    def get_avatar(self, obj):
        if obj.avatar:
            return s.get_selectel_link(str(obj.avatar))
        else:
            # Если нет загруженной фотографии, вернуть ссылку на базовую аватарку
            base_avatar_path = "/users/avatars/base_avatar.jpg"
            return s.get_selectel_link(base_avatar_path)
