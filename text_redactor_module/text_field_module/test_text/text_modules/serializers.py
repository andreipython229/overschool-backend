from .models import MainCourseModel
from rest_framework import serializers


class CustomUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = MainCourseModel
        fields = ['pk', 'name', 'course_text']