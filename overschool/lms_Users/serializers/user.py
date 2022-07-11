from rest_framework import serializers

from lms_User.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('__all__')
