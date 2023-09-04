from courses.models import Section
from courses.serializers import LessonSerializer
from rest_framework import serializers


class SectionSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True, required=False)

    class Meta:
        model = Section
        fields = ["order", "section_id", "course", "name", "lessons"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        lessons_data = data.pop("lessons")
        data["lessons"] = lessons_data
        return data
