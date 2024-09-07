from urllib.parse import urlparse

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from schools.models import Domain, School
from schools.serializers import SchoolBrandingSerializer


class SchoolByDomainView(LoggingMixin, WithHeadersViewSet, APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        domain_name = request.GET.get("domain", None)
        if not domain_name:
            return Response(
                {"error": "Домен не указан"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Найти школу по домену
            parsed_url = urlparse(domain_name)
            current_domain = parsed_url.netloc
            if not current_domain:
                current_domain = parsed_url.path
            domain = Domain.objects.get(domain_name=current_domain)
            school = domain.school

            # Сериализовать школу
            serializer = SchoolBrandingSerializer(school)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Domain.DoesNotExist:
            return Response(
                {"error": "Домен не найден"}, status=status.HTTP_404_NOT_FOUND
            )
