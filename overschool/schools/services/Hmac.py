import hashlib
import hmac
import json

# data = {
#     'order_id': 'xxxx',
#     'customer_phone': '+7xxxxxxxxxx',
#     'customer_email': 'ИМЯ@prodamus.ru',
#     'products': [
#         {
#             'sku': 'XXXXX',
#             'name': 'товар 1',
#             'price': '123',
#             'quantity': 'X',
#             'tax': {
#                 'tax_type': 0,
#                 'tax_sum': 'xx',
#             },
#             'paymentMethod': 'X',
#             'paymentObject': 'X',
#         },
#     ],
#     'do': 'pay',
#     'urlReturn': 'https://demo.payform.ru/demo-return',
#     'urlSuccess': 'https://demo.payform.ru/demo-success',
#     'urlNotification': 'https://demo.payform.ru/demo-notification',
#     'payment_method': 'XX',
#     'discount_value': '0.00',
#     'npd_income_type': 'FROM_INDIVIDUAL',
#     'npd_income_inn': 1234567890,
#     'npd_income_company': 'Название компании плательщика',
#     'link_expired': 'дд.мм.гггг чч:мм',
#     'subscription_date_start': 'дд.мм.гггг чч:мм',
#     'paid_content': 'Текс сообщения'
# }  # Пример структуры данных для формирования подписи

class Hmac:
    @staticmethod
    def create_signature(data, key, algo='sha256'):
        if algo not in hashlib.algorithms_available:
            return False
        transform_data = Hmac.transform_prodamus_link_data(data)
        data = Hmac._str_val_and_sort(transform_data)
        return hmac.new(key.encode(), json.dumps(data, separators=(',', ':'), ensure_ascii=False).encode(),
                        algo).hexdigest()

    @staticmethod
    def verify(data, key, sign, algo='sha256'):
        _sign = Hmac.create(data, key, algo)
        return _sign and _sign.lower() == sign.lower()

    @staticmethod
    def _str_val_and_sort(data):
        if isinstance(data, dict):
            sorted_data = dict(sorted((k, Hmac._str_val_and_sort(v)) for k, v in data.items()))
            return sorted_data
        elif isinstance(data, list):
            sorted_data = [Hmac._str_val_and_sort(item) for item in data]
            return sorted_data
        else:
            return str(data)

    @staticmethod
    def transform_prodamus_link_data(prodamus_payment_link_data: dict) -> dict:

        product_tax = None
        if prodamus_payment_link_data.get("tax_type") is not None and prodamus_payment_link_data.get(
                "tax_sum") is not None:
            product_tax = {"tax_type": prodamus_payment_link_data["tax_type"],
                           "tax_sum": prodamus_payment_link_data["tax_sum"]}

        product = {
            k: v for k, v in {
                "price": prodamus_payment_link_data.get("price"),
                "quantity": str(prodamus_payment_link_data.get("quantity", "")),
                "name": prodamus_payment_link_data.get("name"),
                "sku": prodamus_payment_link_data.get("sku"),
                "tax": product_tax,
                "payment_method": prodamus_payment_link_data.get("payment_method"),
                "payment_object": prodamus_payment_link_data.get("payment_object")
            }.items() if v is not None
        }
        # Фильтрация ключей со значением None
        return {k: v for k, v in {
            "order_id": prodamus_payment_link_data.get("order_id"),
            "customer_phone": prodamus_payment_link_data.get("customer_phone"),
            "customer_email": prodamus_payment_link_data.get("customer_email"),
            "products": [product] if any(product.values()) else [],
            "subscription": prodamus_payment_link_data.get("subscription"),
            "subscription_date_start": prodamus_payment_link_data.get("subscription_date_start"),
            "vk_user_id": prodamus_payment_link_data.get("vk_user_id"),
            "vk_user_name": prodamus_payment_link_data.get("vk_user_name"),
            "customer_extra": prodamus_payment_link_data.get("customer_extra"),
            "do": prodamus_payment_link_data.get("do"),
            "urlReturn": prodamus_payment_link_data.get("urlReturn"),
            "urlSuccess": prodamus_payment_link_data.get("urlSuccess"),
            "urlNotification": prodamus_payment_link_data.get("urlNotification"),
            "sys": prodamus_payment_link_data.get("sys"),
            "discount_value": prodamus_payment_link_data.get("discount_value"),
            "npd_income_type": prodamus_payment_link_data.get("npd_income_type"),
            "npd_income_inn": prodamus_payment_link_data.get("npd_income_inn"),
            "npd_income_company": prodamus_payment_link_data.get("npd_income_company"),
            "link_expired": prodamus_payment_link_data.get("link_expired"),
            "ref": prodamus_payment_link_data.get("ref"),
            "type": prodamus_payment_link_data.get("type"),
            "callbackType": prodamus_payment_link_data.get("callbackType"),
            "currency": prodamus_payment_link_data.get("currency"),
            "payments_limit": prodamus_payment_link_data.get("payments_limit"),
            "acquiring": prodamus_payment_link_data.get("acquiring"),
        }.items() if v is not None}
