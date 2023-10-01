from rest_framework import serializers
from users.models import User


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)

    def validate_email(self, value):
        """
        Checks whether a user with the same email exists in the database
        """
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value