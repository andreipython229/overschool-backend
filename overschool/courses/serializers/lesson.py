from courses.models import Lesson
from rest_framework import serializers


class LessonSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели урока
    """

    class Meta:
        model = Lesson
        fields = "__all__"
