from courses.models.courses.course import CourseAppeals
from rest_framework import serializers


class CourseAppealsSerializer(serializers.ModelSerializer):
    course_name = serializers.SerializerMethodField()

    class Meta:
        model = CourseAppeals
        fields = [
            "id",
            "course",
            "course_name",
            "name",
            "email",
            "phone",
            "message",
            "is_read",
            "created_at",
            "updated_at",
        ]

    def get_course_name(self, obj):
        return obj.course.name
