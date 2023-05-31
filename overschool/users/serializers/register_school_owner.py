from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from users.models import User


class SignupSchoolOwnerSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    phone_number = PhoneNumberField(required=True)
    password = serializers.CharField(write_only=True)
    password_confirmation = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if not attrs.get("email"):
            raise serializers.ValidationError(
                "'email' is required."
            )
        if not attrs.get("phone_number"):
            raise serializers.ValidationError(
                "'phone_number' is required."
            )

        password = attrs.get("password")
        password_confirmation = attrs.get("password_confirmation")
        if password and password != password_confirmation:
            raise serializers.ValidationError("Passwords do not match.")

        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirmation")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.save()
        return instance


