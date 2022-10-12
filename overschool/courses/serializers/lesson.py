from courses.models import Lesson
from rest_framework import serializers


class LessonSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели урока
    """

    class Meta:
        model = Lesson
        fields = ["lesson_id",
                  "section",
                  "name",
                  "order",
                  "description",
                  "video",
                  "points"]
