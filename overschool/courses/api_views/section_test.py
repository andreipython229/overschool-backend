from random import sample

from common_services.apply_swagger_auto_schema import apply_swagger_auto_schema
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from courses.models import (
    Answer,
    BaseLesson,
    Question,
    RandomTestTests,
    Section,
    SectionTest,
    StudentsGroup,
    UserTest,
)
from courses.serializers import (
    QuestionListGetSerializer,
    TestSerializer,
    UserTestSerializer,
)
from courses.services import LessonProgressMixin
from django.db.models import Prefetch
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from schools.models import School
from schools.school_mixin import SchoolMixin

s3 = UploadToS3()


class TestViewSet(
    LoggingMixin,
    WithHeadersViewSet,
    LessonProgressMixin,
    SchoolMixin,
    viewsets.ModelViewSet,
):
    """Эндпоинт просмотра, создания, изменения и удаления тестов\n
    <h2>/api/{school_name}/tests/</h2>\n
    Разрешения для просмотра тестов (любой пользователь)
    Разрешения для создания и изменения тестов (только пользователи с группой 'Admin')"""

    serializer_class = TestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return permissions
        if self.action in [
            "list",
            "retrieve",
            "get_questions",
        ]:
            # Разрешения для просмотра тестов (любой пользователь школы)
            if user.groups.filter(
                group__name__in=["Student", "Teacher"], school=school_id
            ).exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if self.action == "usertests":
            # Разрешения для просмотра попыток прохождения теста учеником
            if user.groups.filter(group__name="Student", school=school_id).exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return (
                SectionTest.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        user = self.request.user
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return SectionTest.objects.filter(section__course__school__name=school_name)

        if user.groups.filter(group__name="Student", school=school_id).exists():
            course_ids = StudentsGroup.objects.filter(
                course_id__school__name=school_name, students=user
            ).values_list("course_id", flat=True)
            return SectionTest.objects.filter(section__course_id__in=course_ids)

        if user.groups.filter(group__name="Teacher", school=school_id).exists():
            course_ids = StudentsGroup.objects.filter(
                course_id_id__school__name=school_name, teacher_id=user.pk
            ).values_list("course_id", flat=True)
            return SectionTest.objects.filter(section__course_id__in=course_ids)

        return SectionTest.objects.none()

    def create(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        section = self.request.data.get("section")
        if section is not None:
            sections = Section.objects.filter(course__school__name=school_name)
            try:
                sections.get(pk=section)
            except sections.model.DoesNotExist:
                raise NotFound(
                    "Указанная секция не относится не к одному курсу этой школы."
                )
        serializer = TestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        section = self.request.data.get("section")
        if section is not None:
            sections = Section.objects.filter(course__school__name=school_name)
            try:
                sections.get(pk=section)
            except sections.model.DoesNotExist:
                raise NotFound(
                    "Указанная секция не относится не к одному курсу этой школы."
                )
        instance = self.get_object()
        serializer = TestSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        base_lesson = BaseLesson.objects.get(tests=instance)
        course = base_lesson.section.course
        school_id = course.school.school_id

        # Получаем список файлов, хранящихся в папке удаляемого теста
        files_to_delete = s3.get_list_objects(
            "{}_school/{}_course/{}_lesson".format(
                school_id, course.course_id, base_lesson.id
            )
        )
        # Удаляем все файлы, связанные с удаляемым тестом
        remove_resp = None
        if files_to_delete:
            if s3.delete_files(files_to_delete) == "Error":
                remove_resp = "Error"

        self.perform_destroy(instance)

        if remove_resp == "Error":
            return Response(
                {"error": "Ошибка удаления ресурса из хранилища Selectel"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["GET"])
    def get_questions(self, request, pk, *args, **kwargs):

        queryset = self.get_queryset()
        try:
            instance = queryset.get(test_id=pk)
        except:
            return Response("Тест не найден")

        # Проверяем пройдены ли предыдущие base_lessons и делаем запись в userprogresslogs
        check_response = self.check_viewed_and_progress_log(request, instance)
        if check_response is not None:
            return check_response

        tests_ids = []

        if instance.random_test_generator:
            num_questions = instance.num_questions

            tests_ids = RandomTestTests.objects.filter(test=instance).values_list(
                "target_test_id", flat=True
            )

            questions_ids = (
                Question.objects.filter(test_id__in=tests_ids)
                .values_list("question_id", flat=True)
                .distinct()
            )

            if len(questions_ids) == 0:
                return Response(
                    {"detail": "random_test_generator=True, Вопросы не найдены."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if len(questions_ids) < num_questions:
                num_questions = len(questions_ids)

            random_question_ids = sample(list(questions_ids), num_questions)
            questions = Question.objects.filter(question_id__in=random_question_ids)
            test_obj = SectionTest.objects.get(baselesson_ptr_id=instance.id).__dict__
        else:
            queryset = self.get_queryset()
            test_obj = queryset.get(test_id=pk).__dict__
            questions = Question.objects.filter(test=pk)

        test = {
            "random_test_generator": test_obj["random_test_generator"],
            "num_questions": test_obj["num_questions"],
            "tests_ids": tests_ids,
            "all_questions": len(questions),
            "test": test_obj["test_id"],
            "test_id": test_obj["test_id"],
            "section": test_obj["section_id"],
            "baselesson_ptr_id": test_obj["baselesson_ptr_id"],
            "type": "test",
            "order": test_obj["order"],
            "name": test_obj["name"],
            "random_questions": test_obj["random_questions"],
            "random_answers": test_obj["random_answers"],
            "points": test_obj["points"],
            "show_right_answers": test_obj["show_right_answers"],
            "attempt_limit": test_obj["attempt_limit"],
            "attempt_count": test_obj["attempt_count"],
            "success_percent": test_obj["success_percent"],
        }
        if test_obj["random_questions"]:
            questions = questions.order_by("?")

        if test_obj["random_answers"]:
            questions = questions.prefetch_related(
                Prefetch("answers", queryset=Answer.objects.order_by("?"))
            )

        questions_ser = QuestionListGetSerializer(questions, many=True)
        test["questions"] = questions_ser.data

        return Response(test)

    @action(detail=True)
    def usertests(self, request, pk, *args, **kwargs):
        """Список попыток прохождения пользователем конкретного теста\n
        <h2>/api/{school_name}/tests/{test_id}/usertests/</h2>\n
        Список попыток прохождения пользователем конкретного теста"""

        test = self.get_object()
        user = self.request.user
        queryset = UserTest.objects.filter(test=test, user=user)
        serializer = UserTestSerializer(queryset, many=True)
        return Response(serializer.data)


TestViewSet = apply_swagger_auto_schema(
    tags=[
        "tests",
    ]
)(TestViewSet)
