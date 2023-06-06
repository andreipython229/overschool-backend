from common_services.yandex_client import get_yandex_link
from rest_framework import serializers
from schools.models import School, SchoolUser


class SchoolSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели школы
    """

    class Meta:
        model = School
        fields = [
            "school_id",
            "name",
            "avatar",
            "avatar_url",
            "order",
            "created_at",
            "updated_at",
        ]


class SchoolGetSerializer(serializers.ModelSerializer):
    """
    Сериализатор просмотра школы
    """

    avatar = serializers.SerializerMethodField()

    class Meta:
        model = School
        fields = [
            "school_id",
            "name",
            "avatar",
            "avatar_url",
            "order",
            "created_at",
            "updated_at",
            "owner",
        ]

    def get_avatar(self, obj):
        return get_yandex_link(str(obj.avatar))
