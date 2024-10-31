from random import sample

from common_services.apply_swagger_auto_schema import apply_swagger_auto_schema
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from courses.models import (
    Answer,
    BaseLesson,
    Course,
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
from django.utils import timezone
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
            "check_timer",
        ]:
            # Разрешения для просмотра тестов (любой пользователь школы)
            if (
                user.groups.filter(
                    group__name__in=["Student", "Teacher"], school=school_id
                ).exists()
                or user.email == "student@coursehub.ru"
            ):
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

    def retrieve(self, request, *args, **kwargs):
        # Получаем тест
        test = self.get_object()
        user = request.user
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        # Проверяем, существует ли уже запись UserTest для данного пользователя и теста
        if UserTest.objects.filter(user=user, test=test, status=True).exists():
            return Response(
                {
                    "status": "Error",
                    "message": "Этот тест уже пройден пользователем",
                },
            )
            # Проверяем, что пользователь является студентом, если нет - просто возвращаем информацию о тесте
        if user.groups.filter(group__name="Student", school=school_id).exists():
            # Создаем или получаем UserTest, если студент еще не проходил тест
            user_test, created = UserTest.objects.get_or_create(
                user=user, test=test, success_percent=0
            )

            # Если тест с таймером и начало еще не зафиксировано, фиксируем его
            if test.has_timer and not user_test.start_time:
                user_test.start_test()  # Запуск таймера, сохраняет start_time

            # Сериализуем и возвращаем информацию о тесте
        serializer = self.get_serializer(test)
        return Response(serializer.data)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return (
                SectionTest.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы

        user = self.request.user
        school_name = self.kwargs.get("school_name")

        try:
            school_id = School.objects.get(name=school_name).school_id
        except School.DoesNotExist:
            return Response(
                {"error": "School not found"}, status=status.HTTP_404_NOT_FOUND
            )

        course_id = self.request.GET.get("courseId")

        if course_id:
            try:
                course = Course.objects.get(course_id=course_id)
                if course.is_copy:
                    original_course = Course.objects.get(
                        name=course.name, is_copy=False
                    )
                    return SectionTest.objects.filter(section__course=original_course)
                else:
                    return SectionTest.objects.filter(section__course=course)
            except Course.DoesNotExist:
                return Response(
                    {"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND
                )

        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return SectionTest.objects.filter(section__course__school__name=school_name)

        if user.groups.filter(group__name="Student", school=school_id).exists():
            course_ids = StudentsGroup.objects.filter(
                course_id__school__name=school_name, students=user
            ).values_list("course_id", flat=True)
            return SectionTest.objects.filter(section__course_id__in=course_ids)

        if user.groups.filter(group__name="Teacher", school=school_id).exists():
            course_ids = StudentsGroup.objects.filter(
                course_id__school__name=school_name, teacher_id=user.pk
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

    @action(detail=True, methods=["get"], url_path="check-timer")
    def check_timer(self, request, *args, **kwargs):
        """
        Проверяет, не истекло ли время прохождения теста.
        """
        user = request.user
        test_id = kwargs.get("pk")

        try:
            # Получаем тест и последний `UserTest` для данного пользователя
            test = SectionTest.objects.get(pk=test_id)
            user_test = (
                UserTest.objects.filter(user=user, test=test)
                .order_by("-created_at")
                .first()
            )

            # Проверяем, задан ли лимит времени для теста
            if not test.time_limit:
                return Response(
                    {"status": "No Timer", "message": "Этот тест без таймера"},
                    status=status.HTTP_200_OK,
                )

            # Проверяем, был ли таймер запущен
            if not user_test or not user_test.start_time:
                return Response(
                    {
                        "status": "Error",
                        "message": "Таймер не был запущен или тест не начат",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Проверяем оставшееся время
            elapsed_time = timezone.now() - user_test.start_time
            if elapsed_time >= test.time_limit:
                return Response(
                    {
                        "status": "Time Expired",
                        "message": "Время прохождения теста истекло",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Вычисляем и возвращаем оставшееся время
            remaining_time = test.time_limit - elapsed_time
            return Response(
                {
                    "status": "Time Remaining",
                    "remaining_time": remaining_time.total_seconds(),
                },
                status=status.HTTP_200_OK,
            )

        except SectionTest.DoesNotExist:
            return Response(
                {"status": "Error", "message": "Тест не найден"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except UserTest.DoesNotExist:
            return Response(
                {"status": "Error", "message": "Не найдено начало теста"},
                status=status.HTTP_404_NOT_FOUND,
            )

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
            "has_timer": test_obj["has_timer"],
            "time_limit": test_obj["time_limit"],
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

        user = self.request.user
        queryset = UserTest.objects.filter(test=pk, user=user)
        serializer = UserTestSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True)
    def previous_tests(self, request, pk, *args, **kwargs):
        """Список предыдущих тестов\n
        <h2>/api/{school_name}/tests/{test_id}/previous_tests/</h2>\n
        Список тестов курса, стоящих по порядку перед данным тестом и доступных для автогенерации на их основе списка вопросов"""

        test = self.get_object()
        section = test.section
        previous_sections_tests = self.get_queryset().filter(
            section__course=section.course, section__order__lt=section.order
        )
        current_section_tests = self.get_queryset().filter(
            section=section, order__lt=test.order
        )
        serializer = TestSerializer(
            previous_sections_tests | current_section_tests, many=True
        )
        return Response(serializer.data)


TestViewSet = apply_swagger_auto_schema(
    tags=[
        "tests",
    ]
)(TestViewSet)
