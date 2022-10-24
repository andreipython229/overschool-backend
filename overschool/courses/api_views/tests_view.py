# -*- coding: utf-8 -*-
from rest_framework import permissions, viewsets

from common_services.mixins import LoggingMixin
from courses.models import Answer, Question, SectionTest, UserTest
from courses.serializers import (AnswerSerializer, QuestionSerializer,
                                 TestSerializer, UserTestSerializer)


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
