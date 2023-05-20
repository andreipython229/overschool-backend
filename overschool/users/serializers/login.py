from django.contrib.auth.hashers import check_password
from django.db.models import Q
from rest_framework import serializers
from users.models import User


class LoginSerializer(serializers.Serializer):
    login = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        value = attrs.get("login")
        password = attrs.get("password")
        user = User.objects.filter(
            Q(username=value) | Q(email=value) | Q(phone_number=value)
        ).first()
        if not user:
            raise serializers.ValidationError("Invalid login credentials")
        if not check_password(password, user.password):
            raise serializers.ValidationError("Invalid password credentials")
        attrs["user"] = user
        return attrs
