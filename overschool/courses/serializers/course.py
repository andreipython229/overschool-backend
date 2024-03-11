from common_services.selectel_client import UploadToS3
from courses.models import Course
from rest_framework import serializers

from .students_group import GroupsInCourseSerializer

s3 = UploadToS3()


class CourseSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели курса
    """

    class Meta:
        model = Course
        fields = [
            "course_id",
            "public",
            "is_catalog",
            "is_direct",
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
            "is_catalog",
            "is_direct",
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
            return s3.get_link(obj.photo.name)
        else:
            # Если нет загруженной картинки, вернуть ссылку на дефолтное изображение
            default_image_path = "base_course.jpg"
            return s3.get_link(default_image_path)


class CourseStudentsSerializer(serializers.Serializer):
    """
    Сериализатор
    """

    course_id = serializers.IntegerField(help_text="Номер курса", required=False)

    class Meta:
        fields = "__all__"


class CourseWithGroupsSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели курса со студенческими группами
    """

    group_course_fk = GroupsInCourseSerializer(many=True)

    class Meta:
        model = Course
        fields = [
            "course_id",
            "public",
            "is_catalog",
            "is_direct",
            "name",
            "format",
            "duration_days",
            "price",
            "description",
            "photo",
            "order",
            "photo_url",
            "school",
            "group_course_fk",
        ]
        read_only_fields = ["order"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["student_groups"] = representation["group_course_fk"]
        del representation["group_course_fk"]
        return representation
