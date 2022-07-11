from django.test import TestCase
import pytest
from .models import Course, Section


@pytest.mark.django_db
def test_user_create():
    Course.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    assert 1 == 1
# Create your tests here.
