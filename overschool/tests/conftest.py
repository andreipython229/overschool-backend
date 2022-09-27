import pytest
from rest_framework.test import APIClient
from users.models import User


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def auth_client(client):
    User.objects.create_user(username="test@gmail.com",
                             email="test@gmail.com",
                             password="W;afd9cx",
                             is_active=True
                             ).save()
    payload = {
        "email": "test@gmail.com",
        "password": "W;afd9cx",
    }
    client.post('/api/login/', payload)
    return client
