from rest_framework import serializers

from lms_User.models import Lesson


class LessonSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели урока
    """

    class Meta:
        model = Lesson
        fields = '__all__'