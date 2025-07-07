from common_services.selectel_client import UploadToS3
from rest_framework import serializers
from schools.models import SchoolNewRole
from users.models import Profile, User, UserGroup

s3 = UploadToS3()

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "patronymic",
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
            user.patronymic = user_data.get("patronymic", user.patronymic)

            new_phone = user_data.get("phone_number")

            if new_phone in (None, ""):
                raise serializers.ValidationError("Нельзя удалить номер телефона.")

            if user.phone_set_by_manager and new_phone != user.phone_number:
                raise serializers.ValidationError("Вы не можете изменить номер, установленный менеджером.")

            user.phone_number = new_phone
            user.save()

            return super().update(instance=instance, validated_data=validated_data)

        instance.avatar = validated_data.get("avatar", instance.avatar)
        instance.city = validated_data.get("city", instance.city)
        instance.sex = validated_data.get("sex", instance.sex)
        instance.description = validated_data.get("description", instance.description)
        instance.save()
        return instance


class UserProfileGetSerializer(serializers.ModelSerializer):
    user = ProfileSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = [
            "profile_id",
            "avatar_url",
            "city",
            "sex",
            "description",
            "user",
        ]
        read_only_fields = fields


class EmailValidateSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
