from rest_framework import serializers
from users.models import UserRole


class AccessDistributionSerializer(serializers.Serializer):
    user_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    emails = serializers.ListField(child=serializers.EmailField(), required=False)
    role = serializers.ChoiceField(required=True, choices=[])
    student_groups = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )
    date = serializers.DateTimeField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        all_roles = list(UserRole.objects.all().values("name"))
        role_choices = [role["name"] for role in all_roles]
        self.fields["role"].choices = role_choices

    def validate(self, attrs):
        if not attrs.get("user_ids") and not attrs.get("emails"):
            raise serializers.ValidationError(
                "Укажите id либо email хотя бы одного пользователя"
            )
        return attrs
