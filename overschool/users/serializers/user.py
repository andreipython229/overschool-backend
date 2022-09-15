from rest_framework import serializers

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=128, min_length=8, write_only=True)

    class Meta:
        model = User
        fields = (
            "email",
            "phone_number",
            "username",
            "password",
            "token",
        )
        read_only_fields = ("token",)


class ChangePasswordSerializer(serializers.Serializer):
    model = User

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
