from rest_framework import serializers

from users.models import User


class UserSerializer(serializers.ModelSerializer):
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
            "user_permissions"
        ]


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "phone_number",
            "password",
            "groups",
            "user_permissions"
        ]
