from courses.models import Course
from rest_framework import serializers


class CourseSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели курса
    """

    class Meta:
        model = Course
        fields = "__all__"
