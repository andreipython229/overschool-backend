from common_services.mixins import LoggingMixin, WithHeadersViewSet
from lesson_tests.models import SectionTest
from lesson_tests.serializers import TestSerializer
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Count, F, Sum
from lesson_tests.models import Question, Answer


class TestViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = SectionTest.objects.all()
    serializer_class = TestSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True)
    def questions(self, request, pk):
        """ Данные по вопросам теста"""
        test_obj = SectionTest.objects.get(test_id=pk).__dict__
        test = {
            "test": test_obj['test_id'],
            "name": test_obj['test_id'],
            "show_right_answers": test_obj['test_id']
        }
        if test_obj['random_questions']:
            questions = Question.objects.filter(test=pk).order_by('?').values("body",
                                                                              "question_id")
        else:
            questions = Question.objects.filter(test=pk).values("body",
                                                                "question_id")
        test['questions'] = list(questions)
        for index, question in enumerate(questions):
            if test_obj['random_answers']:
                answers = Answer.objects.filter(question=question['question_id']).order_by('?').values("answer_id",
                                                                                                    "body")
            else:
                answers = Answer.objects.filter(question=question['question_id']).values("answer_id",
                                                                                      "body")
            test['questions'][index]['answers'] = list(answers)
        return Response(test)
