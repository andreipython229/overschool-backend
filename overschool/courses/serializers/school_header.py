from rest_framework import serializers

from courses.models import SchoolHeader


class SchoolHeaderSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели шапки школы
    """

    class Meta:
        model = SchoolHeader
        fields = [
            "school_id",
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
        ]
