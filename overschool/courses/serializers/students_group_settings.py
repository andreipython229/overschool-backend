from courses.models import StudentsGroupSettings
from rest_framework import serializers


class StudentsGroupSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentsGroupSettings
        fields = [
            "id",
            "strict_task_order",
            "task_submission_lock",
            "submit_homework_to_go_on",
            "submit_test_to_go_on",
            "success_test_to_go_on",
            "overai_lock",
        ]

    def validate(self, attrs):
        order = attrs.get("strict_task_order")
        submit_lock = attrs.get("task_submission_lock")
        submit_homework = attrs.get("submit_homework_to_go_on")
        submit_test = attrs.get("submit_test_to_go_on")
        success_test = attrs.get("success_test_to_go_on")

        if (
            (not order or submit_lock)
            and True in [submit_homework, submit_test, success_test]
            or success_test
            and not submit_test
        ):
            raise serializers.ValidationError(
                "Настройки группы противоречат друг другу"
            )

        return attrs
