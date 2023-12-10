from courses.models import (
    UserLessonSettings,
    UserHomeworkSettings,
    UserTestSettings,
)
from rest_framework import serializers


class UserLessonSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLessonSettings
        fields = '__all__'


class UserHomeworkSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserHomeworkSettings
        fields = '__all__'


class UserTestSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTestSettings
        fields = '__all__'
