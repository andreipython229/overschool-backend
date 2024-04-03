from rest_framework import serializers
from schools.models import TariffPlan


class SubscriptionSerializer(serializers.Serializer):
    tariff = serializers.ChoiceField(choices=TariffPlan.choices)
    days_interval = serializers.IntegerField(default=30, read_only=True)
    pays_count = serializers.IntegerField(required=False)
    promo_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    subscription_type = serializers.ChoiceField(
        choices=[("monthly", "Monthly"), ("upfront", "Upfront")], required=True
    )

    def validate(self, data):
        subscription_type = data.get("subscription_type")
        pays_count = data.get("pays_count")

        if subscription_type == "upfront" and pays_count not in [3, 6, 12]:
            raise serializers.ValidationError(
                "Недопустимый pays_count для предварительной подписки. Должно быть 3, 6 или 12."
            )
        else:
            if subscription_type == "monthly" and pays_count is not None:
                raise serializers.ValidationError(
                    "pays_count не следует указывать для ежемесячной подписки."
                )

        return data
