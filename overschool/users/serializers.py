from rest_framework import serializers
from .models import Feedback, Tariff

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'
        read_only_fields = ['author', 'created_at']

class TariffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tariff
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']