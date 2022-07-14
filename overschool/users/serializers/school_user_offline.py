from rest_framework import serializers

from users.models import SchoolUserOffline


class SchoolUserOfflineSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolUserOffline
        fields = "__all__"
