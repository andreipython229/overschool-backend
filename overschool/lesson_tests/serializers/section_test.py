from rest_framework import serializers

from lesson_tests.models import SectionTest


class TestSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели теста
    """

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
            "balls_per_answer",
            "balls",
            "order",
            "published",
            "author_id"
        ]
