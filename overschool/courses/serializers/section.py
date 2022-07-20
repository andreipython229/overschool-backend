from courses.models import Section
from rest_framework import serializers


class SectionSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели раздела
    """

    class Meta:
        model = Section
        fields = "__all__"
