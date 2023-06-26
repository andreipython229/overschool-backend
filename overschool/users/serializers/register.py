from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from users.models import User
from users.services import SenderServiceMixin


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone_number = PhoneNumberField(required=False)
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
        user.set_password(password)
        user.save()
        return user

    def save(self, **kwargs):
        instance = super().save(**kwargs)
        email = instance.email
        phone_number = instance.phone_number

        if email:
            sender_service = SenderServiceMixin()
            sender_service.send_code_by_email(user=instance, email=email)  # Передайте объект пользователя как аргумент

        if phone_number:
            sender_service = SenderServiceMixin()
            sender_service.send_code_by_phone(phone_number=phone_number, user=instance)

            return instance


class ConfirmationSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)

    def validate(self, attrs):
        code = attrs.get("code")

        if not code:
            raise serializers.ValidationError("Code is required.")

        return attrs


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone_number = PhoneNumberField()

    def validate(self, attrs):
        email = attrs.get("email")
        phone_number = attrs.get("phone_number")

        if not email and not phone_number:
            raise serializers.ValidationError("Either 'email' or 'phone_number' is required.")

        if email and not User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email does not exist.")

        if phone_number and not User.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError("Phone number does not exist.")

        return attrs

    def save(self, **kwargs):
        email = self.validated_data.get("email")
        phone_number = self.validated_data.get("phone_number")

        if email:
            sender_service = SenderServiceMixin()
            sender_service.send_code_by_email(email)

        if phone_number:
            sender_service = SenderServiceMixin()
            sender_service.send_code_by_phone_number(phone_number, user_type=0)  # Provide the appropriate user_type

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
