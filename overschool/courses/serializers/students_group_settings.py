from courses.models import StudentsGroupSettings
from rest_framework import serializers


class StudentsGroupSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentsGroupSettings
        fields = [
            "id",
            "strict_task_order",
            "task_submission_lock",
        ]
