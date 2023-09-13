from rest_framework import serializers
from users.models import User
from users.services import SenderServiceMixin


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)

    password = serializers.CharField(write_only=True)
    password_confirmation = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if not any([attrs.get("email"), attrs.get("phone_number")]):
            raise serializers.ValidationError(
                "At least one of 'email' or 'phone' is required."
            )

        password = attrs.get("password")
        password_confirmation = attrs.get("password_confirmation")
        if password and password != password_confirmation:
            raise serializers.ValidationError("Passwords do not match.")

        email = attrs.get("email")
        phone_number = attrs.get("phone_number")

        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email already exists.")

        if phone_number and User.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError("Phone number already exists.")
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirmation")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)  # Установка пароля с помощью set_password
        user.save()
        return user

    def save(self, **kwargs):
        instance = super().save(**kwargs)
        email = instance.email

        if email:
            sender_service = SenderServiceMixin()
            confirmation_code = sender_service.send_code_by_email(email=email)
            instance.confirmation_code = confirmation_code

        instance.save()
        return instance


class ConfirmationSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    phone_number = serializers.CharField(required=True)

    def validate(self, attrs):
        code = attrs.get("code")
        email = attrs.get("email")
        phone_number = attrs.get("phone_number")

        if not code:
            raise serializers.ValidationError("Code is required.")

        # Дополнительные проверки для почты и номера телефона
        if not email:
            raise serializers.ValidationError("Email is required.")

        if not phone_number:
            raise serializers.ValidationError("Phone number is required.")

        # Вы можете добавить дополнительные проверки на формат почты или номера телефона

        return attrs


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    new_password = serializers.CharField(required=True)

    def validate(self, attrs):
        email = attrs.get("email")
        new_password = attrs.get("new_password")

        if not email:
            raise serializers.ValidationError("Email is required.")

        if not new_password:
            raise serializers.ValidationError("New password is required.")

        return attrs
