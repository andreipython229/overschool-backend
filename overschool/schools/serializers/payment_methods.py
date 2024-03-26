import requests
from rest_framework import serializers
from schools.models import SchoolPaymentMethod
from transliterate import translit


class SchoolPaymentMethodSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели оплаты курсов для школы
    """

    class Meta:
        model = SchoolPaymentMethod
        fields = '__all__'
