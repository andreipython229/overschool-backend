from rest_framework import serializers

from lms_Users.models import Test


class TestSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели теста
    """

    class Meta:
        model = Test
        fields = '__all__'