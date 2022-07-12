from users.serializers import SchoolUserSerializer
from rest_framework import viewsets
from users.models import SchoolUser


class SchoolUserViewSet(viewsets.ModelViewSet):
    queryset = SchoolUser.objects.all()
    serializer_class = SchoolUserSerializer
