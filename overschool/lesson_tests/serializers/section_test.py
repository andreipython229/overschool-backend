from rest_framework import serializers

from lesson_tests.models import SectionTest


class TestSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели теста
    """

    class Meta:
        model = SectionTest
        fields = "__all__"
