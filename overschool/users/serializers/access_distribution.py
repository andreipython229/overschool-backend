from rest_framework import serializers
from users.models import UserRole


class AccessDistributionSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=False)
    email = serializers.EmailField(required=False)
    role = serializers.ChoiceField(required=True, choices=[])
    student_groups = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        all_roles = list(UserRole.objects.all().values("name"))
        role_choices = [role["name"] for role in all_roles]
        self.fields["role"].choices = role_choices

    def validate(self, attrs):
        if not attrs.get("user_id") and not attrs.get("email"):
            raise serializers.ValidationError("Укажите id либо email пользователя")
        return attrs
