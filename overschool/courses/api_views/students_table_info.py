from courses.models import StudentsTableInfo
from courses.serializers import StudentsTableInfoSerializer
from rest_framework import permissions, viewsets


class StudentsTableInfoViewSet(viewsets.ModelViewSet):
    queryset = StudentsTableInfo.objects.all()
    serializer_class = StudentsTableInfoSerializer
    permission_classes = [permissions.DjangoModelPermissions]