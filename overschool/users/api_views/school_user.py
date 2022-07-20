from rest_framework import viewsets
from users.models import SchoolUser
from users.serializers import SchoolUserSerializer


class SchoolUserViewSet(viewsets.ModelViewSet):
    queryset = SchoolUser.objects.all()
    serializer_class = SchoolUserSerializer
