from common_services.yandex_client import get_yandex_link
from rest_framework import serializers
from schools.models import School, SchoolUser

from .school_user import SchoolUserSerializer


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
    owner = serializers.SerializerMethodField()

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

    def get_owner(self, obj):
        try:
            user_scool = SchoolUser.objects.get(school=obj)
            serializer = SchoolUserSerializer(user_scool)
            return serializer.data
        except SchoolUser.DoesNotExixt:
            return None
