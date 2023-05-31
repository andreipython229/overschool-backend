from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from users.models import User
from users.services import SenderServiceMixin


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone = PhoneNumberField(required=False)
    password = serializers.CharField(write_only=True)
    password_confirmation = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if not any([attrs.get("email"), attrs.get("phone")]):
            raise serializers.ValidationError(
                "At least one of 'email' or 'phone' is required."
            )

        password = attrs.get("password")
        password_confirmation = attrs.get("password_confirmation")
        if password and password != password_confirmation:
            raise serializers.ValidationError("Passwords do not match.")

        email = attrs.get("email")
        phone = attrs.get("phone")

        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email already exists.")

        if phone and User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("Phone number already exists.")
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirmation")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def save(self, **kwargs):
        instance = super().save(**kwargs)
        email = instance.email
        phone = instance.phone

        if email:
            sender_service = SenderServiceMixin()
            sender_service.send_code_by_email(email)

        if phone:
            sender_service = SenderServiceMixin()
            sender_service.send_code_by_phone(phone, user_type=0)  # Provide the appropriate user_type

        return instance


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone = PhoneNumberField()

    def validate(self, attrs):
        email = attrs.get("email")
        phone = attrs.get("phone")

        if not email and not phone:
            raise serializers.ValidationError("Either 'email' or 'phone' is required.")

        if email and not User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email does not exist.")

        if phone and not User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("Phone number does not exist.")

        return attrs

    def save(self, **kwargs):
        email = self.validated_data.get("email")
        phone = self.validated_data.get("phone")

        if email:
            sender_service = SenderServiceMixin()
            sender_service.send_code_by_email(email)

        if phone:
            sender_service = SenderServiceMixin()
            sender_service.send_code_by_phone(phone, user_type=0)  # Provide the appropriate user_type

        return super().save(**kwargs)

class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    reset_code = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

    def validate(self, attrs):
        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            raise serializers.ValidationError("New passwords do not match.")

        return attrs
