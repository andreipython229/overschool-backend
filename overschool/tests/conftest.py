import pytest
from rest_framework.test import APIClient

from users.models import User, UserRole

client = APIClient()


@pytest.mark.django_db
def test_login_user():
    User.objects.create_user(
        username="test@gmail.com",
        email="test@gmail.com",
        password="W;afd9cx",
        is_active=True,
        is_superuser=True,
        is_staff=True,
    ).save()
    payload = {
        "email": "test@gmail.com",
        "password": "W;afd9cx",
    }
    response = client.post("/api/login/", payload)
    assert response.status_code == 200


@pytest.mark.django_db
def test_register_user():
    UserRole.objects.create(name="Student", id=1).save()
    payload = dict(
        username="denis",
        email="denis@mail.ru",
        first_name="Dzianis",
        last_name="Kalesnikau",
        phone_number="+375333514878",
        password1="deniska123",
        password2="deniska123",
        group_name="Student",
        id=1,
    )
    response = client.post("/api/register/", payload)
    data = response.data
    print(data)
    assert response.status_code == 201
