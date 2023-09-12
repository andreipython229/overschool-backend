from rest_framework import serializers
from courses.models import StudentsGroupSettings


class StudentsGroupSettingsSerializer(serializers.ModelSerializer):

    # students_group_id = serializers.IntegerField(source='students_group_settings_fk.pk', read_only=True)
    # group_name = serializers.CharField(source='students_group_settings_fk.name', read_only=True)

    class Meta:
        model = StudentsGroupSettings
        fields = [
            # 'students_group_id',
            # 'group_name',
            'id',
            'strict_task_order',
            'task_submission_lock',
        ]