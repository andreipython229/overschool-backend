from common_services.yandex_client import get_yandex_link
from rest_framework import serializers
from schools.models import SchoolHeader


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
            "logo_header",
            "photo_background",
            "favicon",
            "logo_school_url",
            "logo_header_url",
            "photo_background_url",
            "favicon_url",
            "school",
        ]


class SchoolHeaderDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор просмотра конкретной шапки школы
    """

    logo_school = serializers.SerializerMethodField(method_name="get_logo_school_link")
    logo_header = serializers.SerializerMethodField(method_name="get_logo_header_link")
    photo_background = serializers.SerializerMethodField(
        method_name="get_photo_background_link"
    )
    favicon = serializers.SerializerMethodField(method_name="get_favicon_link")

    class Meta:
        model = SchoolHeader
        fields = [
            "header_id",
            "name",
            "description",
            "logo_school",
            "logo_header",
            "photo_background",
            "favicon",
            "logo_school_url",
            "logo_header_url",
            "photo_background_url",
            "favicon_url",
            "school",
        ]
        read_only_fields = [
            "school",
        ]

    def get_logo_school_link(self, obj):
        return get_yandex_link(str(obj.logo_school))

    def get_logo_header_link(self, obj):
        return get_yandex_link(str(obj.logo_header))

    def get_photo_background_link(self, obj):
        return get_yandex_link(str(obj.photo_background))

    def get_favicon_link(self, obj):
        return get_yandex_link(str(obj.favicon))
