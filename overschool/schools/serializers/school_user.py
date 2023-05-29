from schools.models import SchoolUser
from rest_framework import serializers


class SchoolUserSerializer(serializers.ModelSerializer):
    """ Сеиализатор промежуточной модели связи юзера-владельца и школы"""

    class Meta:
        model = SchoolUser
        fields = [
            "school_user_id",
            "school",
            "user",
        ]