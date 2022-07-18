from courses.models import Section
from courses.serializers import SectionSerializer
from rest_framework import permissions, viewsets


class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [permissions.IsAuthenticated]
