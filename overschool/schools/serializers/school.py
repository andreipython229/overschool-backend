from rest_framework import serializers

from schools.models import School, SchoolUser
from .school_user import SchoolUserSerializer

class SchoolSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели школы
    """

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

    def get_owner(self, obj):
        try:
            user_scool = SchoolUser.objects.get(school=obj)
            serializer = SchoolUserSerializer(user_scool)
            return serializer.data
        except SchoolUser.DoesNotExixt:
            return None
