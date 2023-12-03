from common_services.selectel_client import UploadToS3
from rest_framework import serializers
from schools.models import SchoolHeader

s3 = UploadToS3()


class SchoolHeaderSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели шапки школы
    """

    class Meta:
        model = SchoolHeader
        fields = [
            "header_id",
            "name",
            "description",
            "logo_school",
            "photo_background",
            "logo_school_url",
            "photo_background_url",
            "school",
        ]


class SchoolHeaderUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели шапки школы
    """

    class Meta:
        model = SchoolHeader
        fields = [
            "header_id",
            "name",
            "description",
            "logo_school",
            "photo_background",
            "logo_school_url",
            "photo_background_url",
        ]
        read_only_fields = [
            "school",
        ]


class SchoolHeaderDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор просмотра конкретной шапки школы
    """

    logo_school = serializers.SerializerMethodField(method_name="get_logo_school_link")
    photo_background = serializers.SerializerMethodField(
        method_name="get_photo_background_link"
    )

    class Meta:
        model = SchoolHeader
        fields = [
            "header_id",
            "name",
            "description",
            "logo_school",
            "photo_background",
            "logo_school_url",
            "photo_background_url",
            "school",
        ]
        read_only_fields = [
            "school",
        ]

    def get_logo_school_link(self, obj):
        return s3.get_link(obj.logo_school.name) if obj.logo_school else None

    def get_photo_background_link(self, obj):

        if obj.photo_background:
            return s3.get_link(obj.photo_background.name)
        else:
            # Если нет загруженного изображения, вернуть ссылку на изображение по умолчанию
            default_image_path = "base_school.jpg"
            return s3.get_link(default_image_path)
