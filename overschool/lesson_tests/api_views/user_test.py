from common_services.mixins import LoggingMixin, WithHeadersViewSet
from lesson_tests.models import UserTest, SectionTest
from lesson_tests.serializers import UserTestSerializer
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views import View


class TestViewSet(LoggingMixin, WithHeadersViewSet, View):
    queryset = UserTest.objects.all()
    serializer_class = UserTestSerializer
    permission_classes = [permissions.DjangoModelPermissions]

    def post(self, request, *args, **kwargs):
        test = request.data.get("test")
        test_obj = SectionTest.objects.filter(pk=test, questions__answers__status="П").values("questions__answers__pk",
                                                                                              "questions__answers__status",
                                                                                              "questions__pk")

        answers = request.data.get("answers")
