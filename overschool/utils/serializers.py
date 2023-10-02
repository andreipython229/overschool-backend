from rest_framework import serializers
from schools.models import TariffPlan


class SubscriptionSerializer(serializers.Serializer):
    tariff = serializers.ChoiceField(choices=TariffPlan.choices)
    days_interval = serializers.IntegerField(default=30, read_only=True)
    pays_count = serializers.IntegerField(min_value=1)
    promo_code = serializers.CharField(required=False)
