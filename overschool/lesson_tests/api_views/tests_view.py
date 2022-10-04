# -*- coding: utf-8 -*-
from common_services.mixins import LoggingMixin
from courses.models import UserProgressLogs
from lesson_tests.models import Answer, SectionTest, Question, UserTest
from lesson_tests.serializers import (AnswerSerializer, QuestionSerializer,
                                      TestSerializer, UserTestSerializer)
from rest_framework import permissions
from rest_framework import viewsets


class TestViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = SectionTest.objects.all()
    serializer_class = TestSerializer
    permission_classes = [permissions.IsAuthenticated]


class QuestionViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]


class AnswerViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserTestViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = UserTest.objects.all()
    serializer_class = UserTestSerializer
    permission_classes = [permissions.IsAuthenticated]

    # def post(self, request):
    #     user_test = self.get_object()
    #     # if user_test.success_percent>=80:
    #     if user_test.success_percent >= user_test.test.section.success_percent:
    #         UserProgressLogs.objects.bulk_create([UserProgressLogs(user=request.user, section_test=user_test)])
