from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import Answer, Question, SectionTest
from courses.serializers import TestSerializer
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response


class TestViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = SectionTest.objects.all()
    serializer_class = TestSerializer
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action in ["list", "retrieve"]:
            # Разрешения для просмотра текстов (любой пользователь)
            return permissions
        elif self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
            "post_questions",
        ]:
            # Разрешения для создания и изменения тестов (только пользователи с группой 'Admin')
            user = self.request.user
            if user.groups.filter(name="Admin").exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            return permissions

    @action(detail=True, methods=["GET"])
    def get_questions(self, request, pk):
        """Данные по вопросам теста"""
        test_obj = SectionTest.objects.get(test_id=pk).__dict__
        test = {
            "test": pk,
            "name": test_obj["name"],
            "show_right_answers": test_obj["show_right_answers"],
            "attempt_limit": test_obj["attempt_limit"],
            "attempt_count": test_obj["attempt_count"],
        }
        questions = (
            (
                Question.objects.filter(test=pk)
                .order_by("?")
                .values("body", "question_id", "question_type", "body", "picture")
            )
            if test_obj["random_questions"]
            else Question.objects.filter(test=pk).values("body", "question_id")
        )
        test["questions"] = list(questions)
        for index, question in enumerate(questions):
            if test_obj["random_answers"]:
                answers = (
                    Answer.objects.filter(question=question["question_id"])
                    .order_by("?")
                    .values(
                        "answer_id",
                        "body",
                        "question",
                        "picture",
                        "answer_in_range",
                        "from_digit",
                        "to_digit",
                    )
                )
            else:
                answers = Answer.objects.filter(
                    question=question["question_id"]
                ).values("answer_id", "body")
            test["questions"][index]["answers"] = list(answers)
        return Response(test)

    @action(detail=True, methods=["POST"])
    def post_questions(self, request, pk):
        "Создать вопросы в тесте"
        try:
            test_obj = SectionTest.objects.get(test_id=pk)
            questions = request.data.get("questions")
            for question in questions:
                q = Question(
                    test=test_obj,
                    question_type=question["type"],
                    body=question["body"],
                    picture=question["picture"] if "picture" in question else None,
                    is_any_answer_correct=question["is_any_answer_correct"]
                    if "is_any_answer_correct" in question
                    else False,
                    only_whole_numbers=question["only_whole_numbers"]
                    if "only_whole_numbers" in question
                    else False,
                )
                q.save()
                for answer in question["answers"]:
                    a = Answer(
                        question=q,
                        body=answer["body"],
                        status=answer["status"],
                        picture=answer["picture"] if "picture" in answer else None,
                        answer_in_range=answer["answer_in_range"]
                        if "answer_in_range" in answer
                        else False,
                        from_digit=answer["from_digit"]
                        if "from_digit" in answer
                        else 0,
                        to_digit=answer["to_digit"] if "to_digit" in answer else 0,
                    )
                    a.save()
            return Response(data={"status": "OK"}, status=status.HTTP_201_CREATED)
        except Exception:
            return Response(
                data={"status": "Error"}, status=status.HTTP_400_BAD_REQUEST
            )
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
