from rest_framework import serializers
from users.models import User, UserGroup


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
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "id",
            "roles",
        ]

    def get_roles(self, user):
        # Получите все записи UserGroup, связанные с данным пользователем
        user_groups = UserGroup.objects.filter(user=user)
        # Извлеките текстовые идентификаторы групп, связанных с пользователем
        role_names = [user_group.group.name for user_group in user_groups]
        return role_names