from rest_framework import serializers

from courses.models import Lesson


class LessonSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели урока
    """
    type = serializers.CharField(default="lesson", read_only=True)

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
            "type"
        ]
        read_only_fields = ["type"]
