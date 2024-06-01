import re

from rest_framework import serializers

from schools.models import Domain


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ['id', 'domain_name']
        read_only_fields = ['school', 'nginx_configured', 'created_at']

    def validate_domain_name(self, value):
        domain_regex = re.compile(
            r'^(?:[a-zA-Z0-9]'  # Начинается с буквы или цифры
            r'(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+'  # Поддомены
            r'[a-zA-Z]{2,}$'  # Домены верхнего уровня
        )
        if Domain.objects.filter(domain_name=value).exists():
            raise serializers.ValidationError('Domain name already exists')
        if not domain_regex.match(value):
            raise serializers.ValidationError('Invalid domain name.')
        return value

    def update(self, instance, validated_data):
        instance.domain_name = validated_data.get('domain_name', instance.domain_name)
        instance.save()
        return instance

