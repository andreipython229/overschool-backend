import math

from common_services.bepaid_client import bepaid_client
from django.utils import timezone
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
        tariff = data.get("tariff").upper()

        if subscription_type == "upfront" and pays_count not in [3, 6, 12]:
            raise serializers.ValidationError(
                "Недопустимый pays_count для предварительной подписки. Должно быть 3, 6 или 12."
            )
        else:
            if subscription_type == "monthly" and pays_count is not None:
                raise serializers.ValidationError(
                    "pays_count не следует указывать для ежемесячной подписки."
                )

        # Проверка перехода на более высокий тариф
        user_subscription = self.context.get("user_subscription")
        school = self.context.get("school")
        if school:
            current_tariff = school.tariff.name.upper()

            if current_tariff:
                if TariffPlan[tariff] < TariffPlan[current_tariff]:
                    if current_tariff == "JUNIOR" and tariff == "MEDIUM":
                        trial_divisor = 2
                    elif current_tariff == "MEDIUM" and tariff == "SENIOR":
                        trial_divisor = 2
                    elif current_tariff == "JUNIOR" and tariff == "SENIOR":
                        trial_divisor = 4
                    else:
                        raise serializers.ValidationError(
                            "Вы можете перейти только на тариф выше текущего."
                        )
                    if school.purchased_tariff_end_date:
                        # Расчет длительности триала
                        remaining_days = (
                            school.purchased_tariff_end_date - timezone.now()
                        ).days
                        # Если осталось больше 0 дней, берем половину оставшихся дней
                        if remaining_days > 0:
                            trial_days = max(
                                math.ceil(remaining_days / trial_divisor), 0
                            )
                        else:
                            trial_days = 0
                else:
                    trial_days = 0
            else:
                trial_days = 0
            data["trial_days"] = trial_days
        if user_subscription:
            response = bepaid_client.unsubscribe(user_subscription.subscription_id)
            if response.status_code == 200:
                user_subscription.delete()
            else:
                raise serializers.ValidationError("Не удалось отменить подписку")
        return data
