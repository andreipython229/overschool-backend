import requests
from rest_framework import serializers
from schools.models import SchoolPaymentMethod, SchoolPaymentLink, ProdamusPaymentLink
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


class ProdamusLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProdamusPaymentLink
        fields = '__all__'
