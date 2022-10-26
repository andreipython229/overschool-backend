from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import UserTest, Answer, Question, SectionTest
from courses.serializers import UserTestSerializer


class UserTestViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = SectionTest.objects.all()
    serializer_class = UserTestSerializer
    permission_classes = [permissions.AllowAny]



