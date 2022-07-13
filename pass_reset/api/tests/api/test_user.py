import pytest
from rest_framework.test import APIClient

client = APIClient()


@pytest.mark.django_db
def test_register_user():
    payload = dict(
        first_name="Nick",
        last_name="Petrov",
        email="Nick123@gmail.com",
        password="q1w2e3r4t5"

    )

    response = client.post('/api/register/', payload)

    date = response.date

    assert date["first_name"] == payload["first_name"]
    assert date["last_name"] == payload["flast_name"]
    assert "password" not in date
    assert date["email"] == payload["email"]


@pytest.mark.django_db
def test_login_user():
    payload = dict(
        first_name="Nick",
        last_name="Petrov",
        email="Nick123@gmail.com",
        password="q1w2e3r4t5"

    )

    client.post('/api/register/', payload)

    response = client.post("/api/login/", dict(email="Nick123@gmail.com", password="q1w2e3r4t5"))

    assert response.status_code == 200
