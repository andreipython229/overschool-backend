from django.contrib.auth.hashers import check_password
from django.db.models import Q
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User


class LoginSerializer(serializers.Serializer):
    login = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        login = attrs.get("login")
        password = attrs.get("password")
        user = User.objects.filter(Q(email=login) | Q(phone_number=login)).first()

        if not user:
            raise serializers.ValidationError("Invalid login credentials")

        if not check_password(password, user.password):
            raise serializers.ValidationError("Invalid password credentials")

        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]
        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "email": user.email,
            },
        }
