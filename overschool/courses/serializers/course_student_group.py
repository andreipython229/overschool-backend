from rest_framework import serializers

from courses.models import StudentsGroup


class StudentsGroupCourseSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели группы студентов курса
    """
    students_count = serializers.SerializerMethodField()

    class Meta:
        model = StudentsGroup
        fields = ["group_id", "name", "students_count"]

    def get_students_count(self, obj):
        return obj.students.count()