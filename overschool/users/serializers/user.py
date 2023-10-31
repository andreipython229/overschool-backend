from common_services.selectel_client import UploadToS3
from rest_framework import serializers
from users.models import User, UserGroup

s3 = UploadToS3()


class UserSerializer(serializers.ModelSerializer):
    groups = serializers.SerializerMethodField()
    schools = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "last_login",
            "is_superuser",
            "username",
            "first_name",
            "last_name",
            "patronymic",
            "email",
            "phone_number",
            "is_staff",
            "is_active",
            "date_joined",
            "groups",
            "schools",
        ]

    def get_groups(self, obj):
        return obj.groups.values_list("group_id", flat=True)

    def get_schools(self, obj):
        return obj.groups.values_list("school_id", flat=True)


class AllUsersSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "id",
            "role",
            "first_name",
            "last_name",
            "avatar",
        ]

    def get_role(self, user):
        user_group = UserGroup.objects.filter(
            user=user, school=self.context["school"]
        ).first()
        role_name = user_group.group.name
        return role_name

    def get_avatar(self, obj):
        if obj.profile.avatar:
            return s3.get_link(obj.profile.avatar.name)
        else:
            # Если нет загруженной фотографии, вернуть ссылку на базовую аватарку
            base_avatar_path = "users/avatars/base_avatar.jpg"
            return s3.get_link(base_avatar_path)
