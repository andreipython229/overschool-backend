from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from users.models import User


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone_number = PhoneNumberField(required=False)
    password = serializers.CharField(write_only=True)
    password_confirmation = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if not any([attrs.get("email"), attrs.get("phone_number")]):
            raise serializers.ValidationError(
                "At least one of 'email', or 'phone_number' is required."
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
