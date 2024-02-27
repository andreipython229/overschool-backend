from rest_framework import serializers
from users.models import User


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким электронным адресом не существует."
            )
        return value


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    new_password = serializers.CharField(required=True)
    new_password_again = serializers.CharField(required=True)

    def validate(self, attrs):
        new_password = attrs.get("new_password")
        new_password_again = attrs.get("new_password_again")

        if new_password != new_password_again:
            raise serializers.ValidationError("Пароли не совпадают")

        return attrs
