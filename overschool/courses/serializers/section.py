from rest_framework import serializers

from lms_Users.models import Section


class SectionSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели раздела
    """

    class Meta:
        model = Section
        fields = '__all__'
