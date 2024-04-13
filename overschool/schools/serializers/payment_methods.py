import requests
from rest_framework import serializers
from schools.models import SchoolPaymentMethod, SchoolPaymentLink
from transliterate import translit


class SchoolPaymentMethodSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели оплаты курсов для школы
    """

    class Meta:
        model = SchoolPaymentMethod
        fields = '__all__'


class SchoolPaymentLinkSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели ссылки для оплаты курсов для школы
    """

    class Meta:
        model = SchoolPaymentLink
        fields = '__all__'
