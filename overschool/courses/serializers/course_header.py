from rest_framework import serializers

from courses.models import CourseHeader


class CourseHeaderSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели шапки школы
    """

    class Meta:
        model = CourseHeader
        fields = "__all__"
