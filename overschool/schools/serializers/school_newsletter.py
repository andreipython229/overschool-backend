from rest_framework import serializers
from schools.models import NewsletterTemplate


class NewsletterTemplateSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели шаблона для рассылки
    """

    class Meta:
        model = NewsletterTemplate
        fields = "__all__"
