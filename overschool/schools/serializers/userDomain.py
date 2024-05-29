from rest_framework import serializers

from schools.models import Domain


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ['id', 'domain_name', 'nginx_configured', 'created_at']
        read_only_fields = ['school']
