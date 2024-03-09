from courses.models import TrainingDuration
from rest_framework import serializers


class TrainingDurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingDuration
        fields = "__all__"
