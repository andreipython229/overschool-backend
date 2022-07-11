import pytest
from .models import Course

@pytest.mark.django_db
def test_user_create():
    Course.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    assert 1 == 1
