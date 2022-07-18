from django.test import Client, TestCase


class AuthAdminTestCase(TestCase):
    """Абстрактная модель, позволяющая тестировать панель админа, залогинившись админом"""

    fixtures = ["tests/fixtures/users.json"]

    def setUp(self):
        self.client = Client()
        self.client.login(username="testadmin@gmail.com", password="testadmin")

    class Meta:
        abstract = True
