import requests
import json


class BePaidClient:
    def __init__(self, shop_id, secret_key, is_test):
        self.shop_id = shop_id
        self.secret_key = secret_key
        self.is_test = is_test
        self.headers = {'Content-Type': 'application/json'}

    # Добавить параметр trial период
    def subscribe_client(self, to_pay_sum, days_interval, pays_count, first_name, last_name, email, phone):
        to_pay_sum = float(to_pay_sum)
        days_interval = float(days_interval)
        pays_count = float(pays_count)

        payload = json.dumps({
            "test": self.is_test,
            "plan": {
                "currency": "BYN",
                "plan": {
                    "amount": to_pay_sum,
                    "interval": days_interval,
                    "interval_unit": "day"
                },
                "shop_id": self.shop_id,
                "title": "Подписка Тест 123"
            },
            "settings": {
                "language": "ru"
            },
            "customer": {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone,
                "ip": "127.0.0.1"
            },
            "billing_cycles": pays_count,
            "number_payment_attempts": 10
        })
        response = requests.post(
            'https://api.bepaid.by/subscriptions',
            data=payload,
            auth=(self.shop_id, self.secret_key),
            headers=self.headers
        )
        return response.json()

    def get_clients_info(self):
        response = requests.get(
            'https://api.bepaid.by/customers',
            auth=(self.shop_id, self.secret_key),
            headers=self.headers
        )
        return response.json()

    def get_subscription_info(self):
        response = requests.get(
            'https://api.bepaid.by/subscriptions',
            auth=(self.shop_id, self.secret_key),
            headers=self.headers
        )
        return response.json()

    def subscribe_trial_period(self, user_id, plan_id):
        """
        Подписать клиента на тариф с демо-версией.
        :param user_id: Идентификатор пользователя.
        :param plan_id: Идентификатор тарифного плана с демо-версией.
        :return: Ответ от API.
        """
        # логика для подписки на тариф с демо-версией.
        pass

    def unsubscribe(self, user_id):
        """
        Отписать клиента от тарифа.
        :param user_id: Идентификатор пользователя.
        :return: Ответ от API.
        """
        # логика для отписки от тарифа.
        pass

    def recalculate_cost(self, user_id, new_plan_id):
        """
        Перерасчет стоимости при смене тарифа.
        :param user_id: Идентификатор пользователя.
        :param new_plan_id: Идентификатор нового тарифного плана.
        :return: Ответ от API с новой стоимостью и пропорциональной сменой тарифа.
        """
        # логика для перерасчета стоимости при смене тарифа.
        pass

    def get_next_payment_time(self, user_id):
        """
        Получить информацию о времени до следующего платежа.
        :param user_id: Идентификатор пользователя.
        :return: Ответ от API с информацией о времени до следующего платежа.
        """
        # логика для получения информации о времени до следующего платежа.
        pass

bepaid_client = BePaidClient(
    shop_id='21930',
    secret_key='0537f88488ebd20593e0d0f28841630420820aeef1a21f592c9ce413525d9d02',
    is_test=True
)

# 1. Инфо о клиентах
# clients_info = bepaid_client.get_clients_info()
# print(clients_info)

# 2. Подписать клиента на автосписание по тарифу
# subscribe_res = bepaid_client.subscribe_client(
#     to_pay_sum=100,
#     days_interval=30,
#     pays_count=12,
#     first_name='Андрей',
#     last_name='Тест',
#     email='andrei.kozitsky@mail.ru',
#     phone='37533333099'
# trial = ...
# )
# print(subscribe_res['redirect_url'])

# 3. Информация о всех активных подписках
# res = bepaid_client.get_subscription_info()
# print(res)

'''
Логика оплаты
1. 4 тарифа с ограничением по количеству новых учеников в месяц и учеников всего.
Один из этих тарифов полностью бесплатный
2. На бесплатном тарифе есть возможность использовать TRIAL период 14 дней 1 раз 
для аккаунта. Для использования нужно подписаться на 1 из 3-х платных тарифов.
3. Все оплаты делаем через реккурентные платежи/подписочные. Т.Е если карту не отвязать, 
то будут автосписания

Какая логика нужна от API клиента:
1. Подписать клиентна тариф + (Подписать на тариф с демо версией)
2. Отписать клиента от тарифа
3. Логика перерасчёта при смене тарифа (пропорционально стоимостям, 
как с меньшего на больший, так и в обратном порядке)
4. Узнать сколько времени осталось клиенту до следюущего платежа

Скорее всего нам не нужно хранить информацию о сроках платежей и т.д в своей БД,
нам нужно только зафиксировать id тарифного плана для клиента и менять его при смене плана, 
также нужно сделать API для фронта по пунктам выше
'''
