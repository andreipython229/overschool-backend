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
    additional_roles = serializers.SerializerMethodField()

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
            "additional_roles",
        ]

    def get_avatar(self, obj):
        if obj.avatar:
            return s3.get_link(obj.avatar.name)
        else:
            # Если нет загруженной фотографии, вернуть ссылку на базовую аватарку
            base_avatar_path = "users/avatars/base_avatar.jpg"
            return s3.get_link(base_avatar_path)

    def get_additional_roles(self, obj):
        """Получаем словарь с ID школ и списком ролей для каждой школы"""
        user = obj.user
        school_ids = self.get_school_ids_from_user(user)

        if not school_ids:
            return []

        # Для каждой школы находим роли пользователя
        additional_roles_data = []
        for school_id in school_ids:
            additional_roles = SchoolNewRole.objects.filter(
                user=user, school_id=school_id
            ).values_list("role_name", flat=True)

            additional_roles_data.append(
                {"school_id": school_id, "roles": list(additional_roles)}
            )

        return additional_roles_data

    def get_school_ids_from_user(self, user):
        """
        Получаем список ID школ через модель UserGroup
        """
        user_groups = (
            UserGroup.objects.filter(user=user)
            .values_list("school_id", flat=True)
            .distinct()
        )
        return list(user_groups)


class EmailValidateSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
