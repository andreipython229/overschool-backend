from rest_framework import viewsets

from users.models import SchoolUserOffline
from users.serializers import SchoolUserOfflineSerializer


class SchoolUserOfflineViewSet(viewsets.ModelViewSet):
    queryset = SchoolUserOffline.objects.all()
    serializer_class = SchoolUserOfflineSerializer
