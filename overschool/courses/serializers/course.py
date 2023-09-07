from common_services.selectel_client import SelectelClient
from courses.models import Course
from rest_framework import serializers

s = SelectelClient()


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
        read_only_fields = ["order"]


class CourseGetSerializer(serializers.ModelSerializer):
    """
    Сериализатор просмотра курса
    """

    photo = serializers.SerializerMethodField()

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

    def get_photo(self, obj):
        if obj.photo:
            return s.get_selectel_link(str(obj.photo))
        else:
            # Если нет загруженной картинки, вернуть ссылку на дефолтное изображение
            default_image_path = "/base_course.jpg"
            return s.get_selectel_link(default_image_path)


class CourseStudentsSerializer(serializers.Serializer):
    """
    Сериализатор
    """

    course_id = serializers.IntegerField(help_text="Номер курса", required=False)

    class Meta:
        fields = "__all__"
