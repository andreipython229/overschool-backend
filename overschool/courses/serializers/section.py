from courses.models import Section
from rest_framework import serializers
from courses.serializers import LessonSerializer




class SectionSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True)

    class Meta:
        model = Section
        fields = ('section_id', 'course', 'name', 'lessons')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        lessons_data = data.pop('lessons')
        data['lessons'] = lessons_data
        return data
