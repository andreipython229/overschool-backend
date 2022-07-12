from lms_Users.serializers import UserSerializer
from rest_framework import viewsets
from lms_Users.models import User


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
