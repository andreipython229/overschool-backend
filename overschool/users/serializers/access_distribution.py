from rest_framework import serializers
from users.models import UserRole


class AccessDistributionSerializer(serializers.Serializer):
    user_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    emails = serializers.ListField(child=serializers.EmailField(), required=False)
    role = serializers.ChoiceField(required=True, choices=[])
    student_groups = serializers.CharField(required=False)
    date = serializers.DateTimeField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        all_roles = list(UserRole.objects.all().values("name"))
        role_choices = [role["name"] for role in all_roles]
        self.fields["role"].choices = role_choices

    def validate_emails(self, value):
        """Приводим все email-адреса к нижнему регистру"""
        return [email.lower() for email in value]

    def validate(self, attrs):
        if not attrs.get("user_ids") and not attrs.get("emails"):
            raise serializers.ValidationError(
                "Укажите id либо email хотя бы одного пользователя"
            )
        return attrs

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        student_groups_str = data.get("student_groups")
        if isinstance(student_groups_str, str):
            data["student_groups"] = [
                int(group_id.strip()) for group_id in student_groups_str.split(",")
            ]
        elif isinstance(student_groups_str, list):
            # Если student_groups уже является списком строк, преобразуем в целые числа
            data["student_groups"] = [
                int(group_id.strip()) for group_id in student_groups_str
            ]
        return data
