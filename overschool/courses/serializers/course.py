from rest_framework import serializers

from courses.models import Course


class CourseSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели курса
    """

    class Meta:
        model = Course
        fields = "__all__"
