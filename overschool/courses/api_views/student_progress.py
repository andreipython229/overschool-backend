from courses.api_views.schemas import StudentProgressSchemas
from courses.models import (
    BaseLesson,
    Course,
    Homework,
    Lesson,
    SectionTest,
    StudentsGroup,
    UserHomework,
    UserHomeworkCheck,
    UserProgressLogs,
)
from courses.models.homework.homework import Homework
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from schools.models import School
from schools.school_mixin import SchoolMixin


@method_decorator(
    name="get_student_progress_for_student",
    decorator=StudentProgressSchemas.student_progress_for_student_swagger_schema(),
)
class StudentProgressViewSet(SchoolMixin, viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if self.action in [
            "get_student_progress_for_student",
        ]:
            # Разрешения для просмотра статистики (Только Student)
            if user.groups.filter(
                group__name__in=[
                    "Student",
                ],
                school=school_id,
            ).exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        elif self.action in [
            "get_student_progress_by_id",
        ]:
            # Разрешения для просмотра статистики по id (Только Admin этой школы)
            if user.groups.filter(
                group__name__in=[
                    "Admin",
                ],
                school=school_id,
            ).exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    @action(detail=False, methods=["get"])
    def get_student_progress_for_student(self, request, **kwargs):
        """
        Прогресс по студенту сделавшему запрос\n
        """
        user = request.user
        school_name = kwargs.get("school_name")
        course_id = request.query_params.get("course_id")

        return self.generate_response(
            student=user, school_name=school_name, course_id=course_id
        )

    def generate_response(self, school_name, student, course_id):
        school_id = School.objects.get(name=school_name).school_id

        all_base_lesson_ids = UserProgressLogs.objects.filter(
            user=student.pk
        ).values_list("lesson_id", flat=True)

        return_dict = {}

        try:
            if student.groups.filter(group__name="Student", school=school_id).exists():
                StudentsGroup.objects.get(
                    course_id__school__name=school_name,
                    students=student,
                    course_id=course_id,
                )
        except StudentsGroup.DoesNotExist:
            return Response(
                "Студент не найден в указанном курсе.",
                status=status.HTTP_403_FORBIDDEN,
            )

        course = {}
        course_obj = Course.objects.get(pk=course_id)
        all_base_lesson = BaseLesson.objects.filter(section_id__course_id=course_id)
        all_base_completed_lesson = BaseLesson.objects.filter(
            pk__in=all_base_lesson_ids, section_id__course_id=course_id
        )

        course["course_id"] = course_obj.pk
        course["course_name"] = course_obj.name
        course["all_baselessons"] = all_base_lesson.count()
        course["completed_count"] = all_base_completed_lesson.count()
        course["completed_perсent"] = (
            round(all_base_completed_lesson.count() / all_base_lesson.count() * 100, 2)
            if all_base_completed_lesson.count() != 0
            else 0
        )

        all_lessons = Lesson.objects.filter(section_id__course_id=course_id)
        all_homeworks = Homework.objects.filter(section_id__course_id=course_id)
        all_tests = SectionTest.objects.filter(section_id__course_id=course_id)

        completed_lessons = all_lessons.filter(
            baselesson_ptr_id__in=all_base_lesson_ids
        )
        completed_homeworks = all_homeworks.filter(
            baselesson_ptr_id__in=all_base_lesson_ids
        )
        completed_tests = all_tests.filter(baselesson_ptr_id__in=all_base_lesson_ids)

        course["lessons"] = dict(
            completed_perсent=round(
                completed_lessons.count() / all_lessons.count() * 100, 2
            )
            if completed_lessons.count() != 0
            else 0,
            all_lessons=all_lessons.count(),
            completed_lessons=completed_lessons.count(),
        )
        course["homeworks"] = dict(
            completed_perсent=round(
                completed_homeworks.count() / all_homeworks.count() * 100, 2
            )
            if completed_lessons.count() != 0
            else 0,
            all_homeworks=all_homeworks.count(),
            completed_homeworks=completed_homeworks.count(),
        )
        course["tests"] = dict(
            completed_perсent=round(
                completed_tests.count() / all_tests.count() * 100, 2
            )
            if completed_tests.count() != 0
            else 0,
            all_tests=all_tests.count(),
            completed_tests=completed_tests.count(),
        )

        return_dict["student"] = student.email
        return_dict["school_id"] = school_id
        return_dict["school_name"] = school_name
        return_dict["course"] = course

        return Response(return_dict)
