from rest_framework import serializers
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    groups = serializers.SerializerMethodField()
    schools = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "last_login",
            "is_superuser",
            "username",
            "first_name",
            "last_name",
            "patronymic",
            "email",
            "phone_number",
            "is_staff",
            "is_active",
            "date_joined",
            "groups",
            "schools",

        ]

    def get_groups(self, obj):
        return obj.groups.values_list("group_id", flat=True)

    def get_schools(self, obj):
        return obj.groups.values_list("school_id", flat=True)


class AllUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "id",

        ]
