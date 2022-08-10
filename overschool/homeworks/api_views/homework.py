from common_services.mixins import WithHeadersViewSet
from homeworks.models import Homework
from homeworks.serializers import HomeworkSerializer
from rest_framework import permissions, viewsets


class HomeworkViewSet(WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = Homework.objects.all()
    serializer_class = HomeworkSerializer
    permission_classes = [permissions.DjangoModelPermissions]
