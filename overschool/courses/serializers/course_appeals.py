from courses.models.courses.course import CourseAppeals
from rest_framework import serializers


class CourseAppealsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseAppeals
        fields = "__all__"
