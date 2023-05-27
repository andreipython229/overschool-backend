from rest_framework import serializers

from courses.models import Course


class CourseSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели курса
    """

    class Meta:
        model = Course
        fields = [
            "course_id",
            "public",
            "name",
            "format",
            "duration_days",
            "price",
            "description",
            "photo",
            "order",
            "photo_url",
            "school",
        ]


class CourseStudentsSerializer(serializers.Serializer):
    """
    Сериализатор
    """

    course_id = serializers.IntegerField(help_text="Номер курса", required=False)

    class Meta:
        fields = "__all__"
