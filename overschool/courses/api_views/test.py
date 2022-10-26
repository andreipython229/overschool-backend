from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import Answer, Question, SectionTest
from courses.serializers import TestSerializer


class TestViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = SectionTest.objects.all()
    serializer_class = TestSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True, methods=['GET'])
    def get_questions(self, request, pk):
        """Данные по вопросам теста"""
        test_obj = SectionTest.objects.get(test_id=pk).__dict__
        test = {
            "test": test_obj["test_id"],
            "name": test_obj["test_id"],
            "show_right_answers": test_obj["test_id"],
        }
        questions = (
            Question.objects.filter(test=pk)
            .order_by("?")
            .values("body", "question_id")
        ) if test_obj["random_questions"] else Question.objects.filter(test=pk).values("body", "question_id")
        test["questions"] = list(questions)
        for index, question in enumerate(questions):
            if test_obj["random_answers"]:
                answers = (
                    Answer.objects.filter(question=question["question_id"])
                    .order_by("?")
                    .values("answer_id", "body")
                )
            else:
                answers = Answer.objects.filter(
                    question=question["question_id"]
                ).values("answer_id", "body")
            test["questions"][index]["answers"] = list(answers)
        return Response(test)

    @action(detail=True, methods=['POST'])
    def post_questions(self, request, pk):
        "Создать вопросы в тесте"
        try:
            test_obj = SectionTest.objects.get(test_id=pk)
            questions = request.data['questions']
            for question in questions:
                q = Question(test=test_obj,
                             question_type=question['type'],
                             body=question['body'],
                             picture=question['picture'] if 'picture' in question else None,
                             is_any_answer_correct=question[
                                 'is_any_answer_correct'] if 'is_any_answer_correct' in question else None,
                             only_whole_numbers=question[
                                 'only_whole_numbers'] if 'only_whole_numbers' in question else None)
                q.save()
                for answer in question['answers']:
                    a = Answer(question=q,
                               body=answer['body'],
                               status=answer['status'],
                               picture=answer['picture'] if 'picture' in answer else None,
                               answer_in_range=answer['answer_in_range'] if 'answer_in_range' in answer else False,
                               from_digit=answer['from_digit'] if 'from_digit' in answer else 0,
                               to_digit=answer['to_digit'] if 'to_digit' in answer else 0)
                    a.save()
            return Response(data={"status": "OK"},
                            status=status.HTTP_201_CREATED)
        except Exception:
            return Response(data={"status": "Error"},
                            status=status.HTTP_400_BAD_REQUEST)
        # Question.objects.bulk_create(
        #     [Question(test=test_obj,
        #               question_type=question['type'],
        #               body=question['body'],
        #               picture=question['picture'] if 'picture' in question else None,
        #               is_any_answer_correct=question[
        #                   'is_any_answer_correct'] if 'is_any_answer_correct' in question else None,
        #               only_whole_numbers=question['only_whole_numbers'] if 'only_whole_numbers' in question else None)
        #      for question in questions]
        # )
