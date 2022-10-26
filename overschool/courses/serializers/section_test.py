from rest_framework import serializers

from courses.models import SectionTest


class TestSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели теста
    """
    type = serializers.CharField(default="test", read_only=True)

    class Meta:
        model = SectionTest
        fields = [
            "test_id",
            "section",
            "name",
            "success_percent",
            "random_questions",
            "random_answers",
            "show_right_answers",
            "attempt_limit",
            "attempt_count",
            "points_per_answer",
            "points",
            "order",
            "author_id",
            "type"
        ]
        read_only_fields = ["type"]
