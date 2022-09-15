from django.contrib.auth import authenticate
from rest_framework import serializers

from users.models import User


class RegistrationSerializer(serializers.ModelSerializer):
    """Сериализация регистрации пользователя и создания нового."""

    class Meta:
        model = User
        fields = ["username", "email", "phone_number", "password"]
        extra_kwargs = {"password": {"write_only": True}}

        def create(self, validated_data):
            password = validated_data.pop("password", None)
            instance = self.Meta.model(**validated_data)
            if password:
                instance.set_password(password)
            instance.save()
            return instance


class RegisterAdminSerializer(serializers.Serializer):
    sender_type = serializers.CharField(
        max_length=10,
        required=True,
        error_messages={"required": "No sender type sent"},
        help_text="Тип отправки сообщения с урлом и токеном может быть либо mail либо phone",
    )
    recipient = serializers.CharField(
        max_length=256,
        required=True,
        error_messages={"required": "No recipient sent"},
        help_text="Телефон или почта того, кого регистрируют",
    )
    user_type = serializers.IntegerField(
        required=True,
        error_messages={"required": "No user type sent"},
        help_text="Айди роли пользователя",
    )
    course_id = serializers.IntegerField(
        required=True,
        error_messages={"required": "No course id sent"},
        help_text="Айди курса, на которого регистрируют пользователя",
    )


class FirstRegisterSerializer(serializers.Serializer):
    token = serializers.CharField(
        max_length=256,
        required=True,
        error_messages={"required": "No token"},
        help_text="Токен, полученный при регистрации пользователя админом",
    )


class LoginPrSerializer(serializers.Serializer):
    password = serializers.CharField(
        max_length=256,
        required=True,
        error_messages={"required": "No password"},
        help_text="Пароль пользователя",
    )
    email = serializers.EmailField(
        required=True,
        error_messages={"required": "No email"},
        help_text="Почта пользователя",
    )


class LoginSerializer(serializers.Serializer):
    """Сериализатор входа в свою учетную запись."""

    username = serializers.CharField(max_length=255)
    email = serializers.CharField(max_length=255, read_only=True)
    phone_number = serializers.CharField(max_length=128, read_only=True)
    password = serializers.CharField(max_length=128, write_only=True)
    token = serializers.CharField(max_length=255, read_only=True)

    def create(self, data):
        username = data.get("username", None)
        password = data.get("password", None)

        if username is None:
            raise serializers.ValidationError("Для входа требуется имя пользователя.")

        if password is None:
            raise serializers.ValidationError("Для входа требуется пароль.")

        user = authenticate(username=username, password=password)

        if user is None:
            raise serializers.ValidationError(
                "Пользователь с таким адресом электронной почты и паролем не найден."
            )

        if not user.is_active:
            raise serializers.ValidationError("Этот пользователь был деактивирован.")

        return {
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number,
            "token": user.token,
        }
