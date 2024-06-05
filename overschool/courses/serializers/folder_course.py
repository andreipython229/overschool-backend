from courses.models import Course, Folder
from courses.serializers import CourseSerializer
from rest_framework import serializers


class FolderCourseSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели папки курса
    """

    class Meta:
        model = Folder
        fields = ["id", "name", "school"]
        read_only_fields = ["school"]


class FolderViewSerializer(serializers.ModelSerializer):
    """
    Сериализатор просмотра папки курса
    """

    courses = serializers.SerializerMethodField()

    class Meta:
        model = Folder
        fields = "__all__"

    def get_courses(self, obj):
        courses = Course.objects.filter(folder=obj)
        return CourseSerializer(courses, many=True).data
