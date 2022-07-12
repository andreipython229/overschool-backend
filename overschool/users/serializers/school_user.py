from rest_framework import serializers

from users.models import SchoolUser


class SchoolUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolUser
        fields = ('__all__')
