from rest_framework import serializers

from courses.models import Lesson


class LessonSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели урока
    """

    class Meta:
        model = Lesson
        fields = [
            "lesson_id",
            "section",
            "name",
            "order",
            "description",
            "video",
            "points",

        ]
