from common_services.selectel_client import UploadToS3
from courses.models import Course
from courses.serializers import SectionSerializer
from rest_framework import serializers

s3 = UploadToS3()


class CourseCatalogSerializer(serializers.ModelSerializer):
    """
    Сериализатор каталога курсов
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


class CourseCatalogDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор каталога курса
    """

    photo = serializers.SerializerMethodField()
    sections = SectionSerializer(many=True, read_only=True)
    contact_link = serializers.ReadOnlyField(source="school.contact_link")

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
            "photo_url",
            "school",
            "sections",
            "contact_link",
        ]

    def get_photo(self, obj):
        if obj.photo:
            return s3.get_link(obj.photo.name)
        else:
            # Если нет загруженной картинки, вернуть ссылку на дефолтное изображение
            default_image_path = "base_course.jpg"
            return s3.get_link(default_image_path)
