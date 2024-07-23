from rest_framework import serializers
from users.models import User


class StudentRatingSerializer(serializers.ModelSerializer):
    completed_lessons = serializers.IntegerField(required=False)
    available_courses = serializers.IntegerField(required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "completed_lessons",
            "available_courses",
        ]
