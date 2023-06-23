from rest_framework import serializers
from users.models import UserRole


class AccessDistributionSerializer(serializers.Serializer):
    all_roles = list(UserRole.objects.all().values("name"))
    ROLES = [role["name"] for role in all_roles]

    user_id = serializers.IntegerField(required=True)
    role = serializers.ChoiceField(required=True, choices=ROLES)
    student_groups = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )
