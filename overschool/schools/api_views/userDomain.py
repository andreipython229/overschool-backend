from rest_framework import viewsets, permissions
from rest_framework.response import Response
from schools.models import Domain, School
from schools.serializers import DomainSerializer


class DomainViewSet(viewsets.ModelViewSet):
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)

        if user.groups.filter(group__name="Admin", school=school).exists():
            return self.queryset.filter(school=school)
        else:
            return self.queryset.none()

    def perform_create(self, serializer):
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)
        serializer.save(school=school)


class UnconfiguredDomainViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        unconfigured_domains = Domain.objects.filter(nginx_configured=False)
        serializer = DomainSerializer(unconfigured_domains, many=True)
        return Response(serializer.data)