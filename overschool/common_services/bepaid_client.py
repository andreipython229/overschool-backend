import json

import requests
from django.conf import settings


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


class BePaidClient:
    def __init__(self, shop_id, secret_key, is_test):
        self.shop_id = shop_id
        self.secret_key = secret_key
        self.is_test = is_test
        self.headers = {"Content-Type": "application/json"}

    def subscribe_client(
        self,
        request,
        to_pay_sum,
        days_interval,
        first_name,
        last_name,
        email,
        phone,
        tariff,
        school,
        promo_code: str | None,
        trial_days: int | None = None,
    ):
        to_pay_sum = float(to_pay_sum)
        days_interval = float(days_interval)

        payload = {
            "additional_data": {
                "tariff": tariff,
                "school": school,
                "promo_code": promo_code,
                "trial_days": trial_days,
            },
            "plan": {
                "test": self.is_test,
                "currency": "BYN",
                "plan": {
                    "amount": to_pay_sum,
                    "interval": days_interval,
                    "interval_unit": "day",
                },
                "shop_id": self.shop_id,
                "title": f"Подписка на тарифный план школы - {tariff}",
                "language": "ru",
                "infinite": True,
                "billing_cycles": None,
                "number_payment_attempts": 3,
            },
            "return_url": f"https://overschool.by/school/{school}/tariff-plans",
            "notification_url": settings.NOTIFICATION_URL_BEPAID,
            "settings": {"language": "ru"},
            "customer": {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone,
                "ip": get_client_ip(request),
            },
        }

        # Добавление информации о бесплатном триальном периоде, если он задан
        if trial_days is not None:
            payload["plan"]["trial"] = {
                "amount": 0,  # Установка стоимости триала в 0
                "interval": trial_days,
                "interval_unit": "day",
                "as_first_payment": True,
            }

        payload_json = json.dumps(payload)
        response = requests.post(
            "https://api.bepaid.by/subscriptions",
            data=payload_json,
            auth=(self.shop_id, self.secret_key),
            headers=self.headers,
        )
        return response.json()

    def get_clients_info(self):
        response = requests.get(
            "https://api.bepaid.by/customers",
            auth=(self.shop_id, self.secret_key),
            headers=self.headers,
        )
        return response.json()

    def get_subscription_info(self):
        response = requests.get(
            "https://api.bepaid.by/subscriptions",
            auth=(self.shop_id, self.secret_key),
            headers=self.headers,
        )
        return response.json()

    def get_subscription_status(self, subscription_id):
        response = requests.get(
            f"https://api.bepaid.by/subscriptions/{subscription_id}",
            auth=(self.shop_id, self.secret_key),
            headers=self.headers,
        )
        return response.json()

    def unsubscribe(self, subscription_id):
        response = requests.delete(
            f"https://api.bepaid.by/subscriptions/{subscription_id}",
            auth=(self.shop_id, self.secret_key),
            headers=self.headers,
        )
        # Возвращаем пустой словарь, так как отписка не возвращает данные
        return {}


bepaid_client = BePaidClient(
    shop_id=settings.BEPAID_SHOP_ID,
    secret_key=settings.BEPAID_SECRET_KEY,
    is_test=True,
)
