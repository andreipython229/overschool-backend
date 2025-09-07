from rest_framework import serializers
from ..models import Tariff

class TariffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tariff
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']