from datetime import datetime

from common_services.selectel_client import UploadToS3
from courses.api_views.schemas import StudentProgressSchemas
from courses.models import (
    BaseLesson,
    Course,
    CourseCopy,
    Lesson,
    SectionTest,
    StudentsGroup,
    StudentsHistory,
    UserHomework,
    UserProgressLogs,
)
from courses.models.homework.homework import Homework
from django.core.exceptions import PermissionDenied
from django.db.models import Avg
from django.utils.decorators import method_decorator
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from schools.models import School
from schools.school_mixin import SchoolMixin
from tg_notifications.services import CompletedCourseNotifications
from users.models import User

s3 = UploadToS3()


@method_decorator(
    name="get_student_progress_for_student",
    decorator=StudentProgressSchemas.student_progress_for_student_swagger_schema(),
)
@method_decorator(
    name="homework_progress",
    decorator=StudentProgressSchemas.homework_progress_swagger_schema(),
)
@method_decorator(
    name="all_courses_progress",
    decorator=StudentProgressSchemas.all_courses_progress_swagger_schema(),
)
@method_decorator(
    name="get_student_progress_for_admin_or_teacher",
    decorator=StudentProgressSchemas.student_progress_for_admin_or_teacher_swagger_schema(),
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
        if self.action in ["all_courses_progress"]:
            if (
                user.groups.filter(
                    group__name__in=[
                        "Student",
                        "Admin",
                    ],
                    school=school_id,
                ).exists()
                or user.email == "student@coursehub.ru"
            ):
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if self.action in ["homework_progress"]:
            if (
                user.groups.filter(
                    group__name__in=[
                        "Student",
                        "Admin",
                    ],
                    school=school_id,
                ).exists()
                or user.email == "student@coursehub.ru"
            ):
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        elif self.action in [
            "get_student_progress_for_student",
        ]:
            # Разрешения для просмотра статистики (Только Student)
            if (
                user.groups.filter(
                    group__name__in=[
                        "Student",
                    ],
                    school=school_id,
                ).exists()
                or user.email == "student@coursehub.ru"
            ):
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        elif self.action in [
            "get_student_progress_for_admin_or_teacher",
        ]:
            # Разрешения для просмотра статистики по id (Только Admin этой школы)
            if user.groups.filter(
                group__name__in=[
                    "Admin",
                    "Teacher",
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
        school_id = School.objects.get(name=school_name).school_id

        try:
            StudentsGroup.objects.get(
                students=user,
                course_id=course_id,
                course_id__school__school_id=school_id,
            )
        except:
            return Response(
                f"Студент в курсе course_id = {course_id} не найден.",
                status=status.HTTP_403_FORBIDDEN,
            )

        return self.generate_response(
            student=user, school_name=school_name, courses_ids=[int(course_id)]
        )

    @action(detail=False, methods=["get"])
    def get_student_progress_for_admin_or_teacher(self, request, **kwargs):
        """
        Прогресс по студенту для Админа и Учителя\n
        """
        user = request.user
        school_name = kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
        student_id = request.query_params.get("student_id")

        try:
            student = User.objects.get(pk=student_id)
            if not student.groups.filter(
                group__name="Student", school=school_id
            ).exists():
                return Response(
                    f"student_id не принадлежит пользователю добавленному как студент в данную школу.",
                    status=status.HTTP_403_FORBIDDEN,
                )
        except:
            return Response(
                f"Студент с id = {student_id} не найден.",
                status=status.HTTP_403_FORBIDDEN,
            )

        courses_ids = []

        if (
            student.groups.filter(group__name="Student", school=school_id).exists()
            and user.groups.filter(group__name="Admin", school=school_id).exists()
        ):
            courses_ids = StudentsGroup.objects.filter(
                course_id__school__name=school_name, students=student_id
            ).values_list("course_id", flat=True)
        elif (
            student.groups.filter(group__name="Student", school=school_id).exists()
            and user.groups.filter(group__name="Teacher", school=school_id).exists()
        ):
            courses_ids = StudentsGroup.objects.filter(
                course_id__school__name=school_name,
                students=student_id,
                teacher_id_id=user.pk,
            ).values_list("course_id", flat=True)

        return self.generate_response(
            student=student,
            school_name=school_name,
            courses_ids=courses_ids,
        )

    @action(detail=False, methods=["get"])
    def homework_progress(self, request, **kwargs):
        """Генерирует статистику для заданного курса по домашним заданиям"""

        user = request.user
        school_name = kwargs.get("school_name")
        course_id = request.query_params.get("course_id")
        school_id = School.objects.get(name=school_name).school_id

        is_student = StudentsGroup.objects.filter(
            students=user,
            course_id=course_id,
            course_id__school__school_id=school_id,
        ).exists()

        if (
            not is_student
            and not user.groups.filter(group__name="Admin", school=school_id).exists()
        ):
            return Response(
                f"Студент в курсе course_id = {course_id} не найден.",
                status=status.HTTP_403_FORBIDDEN,
            )
        return self.generate_response(
            student=user, school_name=school_name, courses_ids=[int(course_id)]
        )

    @action(detail=False, methods=["get"])
    def all_courses_progress(self, request, **kwargs):
        """Генерирует статистику всех курсов по домашним заданиям"""

        user = request.user
        school_name = kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        all_courses = Course.objects.filter(school__school_id=school_id)

        is_admin = user.groups.filter(group__name="Admin", school=school_id).exists()
        is_student = StudentsGroup.objects.filter(
            students=user, course_id__in=all_courses
        ).exists()

        if not is_student and not is_admin:
            return Response(
                f"Студент в одном из курсов школы {school_name} не найден.",
                status=status.HTTP_403_FORBIDDEN,
            )

        courses_ids = [course.course_id for course in all_courses]

        return self.all_courses_progress_response(
            student=user, school_name=school_name, courses_ids=courses_ids
        )

    def generate_response(self, school_name, student, courses_ids):
        """Генерирует статистику по студенту по всем курсам в школе"""

        school_id = School.objects.get(name=school_name).school_id
        courses = []
        return_dict = {
            "student": student.email,
            "school_id": school_id,
            "school_name": school_name,
            "courses": courses,
        }
        for course_id in courses_ids:
            course_obj = Course.objects.get(pk=course_id)
            student_group = StudentsGroup.objects.filter(
                students__id=student.pk, course_id=course_id
            ).first()

            if course_obj.is_copy:
                original_course_obj = CourseCopy.objects.get(
                    course_copy_id=course_obj.course_id
                )
                course_id = (
                    original_course_obj.course_id if original_course_obj else course_id
                )

            all_base_lessons = BaseLesson.objects.filter(
                section_id__course_id=course_id, active=True
            ).exclude(lessonavailability__student=student)

            lesson_viewed_ids = UserProgressLogs.objects.filter(
                lesson_id__in=all_base_lessons.values("id"), user_id=student
            ).values_list("lesson_id", flat=True)

            lesson_completed_ids = UserProgressLogs.objects.filter(
                lesson_id__in=all_base_lessons.values("id"),
                completed=True,
                user_id=student,
            ).values_list("lesson_id", flat=True)

            all_lessons = (
                Lesson.objects.filter(section_id__course_id=course_id, active=True)
                .exclude(lessonavailability__student=student)
                .exclude(lessonenrollment__student_group=student_group.pk)
            )

            all_homeworks = (
                Homework.objects.filter(section_id__course_id=course_id, active=True)
                .exclude(lessonavailability__student=student)
                .exclude(lessonenrollment__student_group=student_group.pk)
            )

            all_tests = (
                SectionTest.objects.filter(section_id__course_id=course_id, active=True)
                .exclude(lessonavailability__student=student)
                .exclude(lessonenrollment__student_group=student_group.pk)
            )

            completed_lessons = all_lessons.filter(
                baselesson_ptr_id__in=lesson_viewed_ids
            )

            completed_homeworks = all_homeworks.filter(
                baselesson_ptr_id__in=lesson_completed_ids
            )

            completed_tests = all_tests.filter(
                baselesson_ptr_id__in=lesson_completed_ids
            )

            completed_all = (
                completed_lessons.count()
                + completed_homeworks.count()
                + completed_tests.count()
            )

            progress_percent = self.calculate_progress(
                completed_all, all_base_lessons.count()
            )

            average_mark = (
                UserHomework.objects.filter(
                    user=student, homework__section__course_id=course_id
                ).aggregate(average_mark=Avg("mark"))["average_mark"]
                or 0
            )

            # Получаем всех студентов курса и вычисляем их прогресс
            all_students = StudentsGroup.objects.filter(
                course_id=course_id
            ).values_list("students", flat=True)
            students_progress = []

            for student_id in all_students:
                if student_id is None:
                    continue
                student_obj = User.objects.get(pk=student_id)
                lesson_viewed_ids = UserProgressLogs.objects.filter(
                    lesson_id__in=all_base_lessons.values("id"), user_id=student_obj
                ).values_list("lesson_id", flat=True)

                lesson_completed_ids = UserProgressLogs.objects.filter(
                    lesson_id__in=all_base_lessons.values("id"),
                    completed=True,
                    user_id=student_obj,
                ).values_list("lesson_id", flat=True)

                completed_all_for_student = (
                    all_lessons.filter(baselesson_ptr_id__in=lesson_viewed_ids).count()
                    + all_homeworks.filter(
                        baselesson_ptr_id__in=lesson_completed_ids
                    ).count()
                    + all_tests.filter(
                        baselesson_ptr_id__in=lesson_completed_ids
                    ).count()
                )

                progress_for_student = self.calculate_progress(
                    completed_all_for_student, all_base_lessons.count()
                )

                students_progress.append(
                    {
                        "student": student_obj,
                        "progress_percent": progress_for_student,
                    }
                )

                # Сортируем студентов по прогрессу
            students_progress.sort(key=lambda x: x["progress_percent"], reverse=True)

            # Определяем место текущего студента
            student_rank = next(
                (
                    index
                    for index, entry in enumerate(students_progress, start=1)
                    if entry["student"].pk == student.pk
                ),
                None,
            )

            # Получаем первых трех лидеров
            top_leaders = students_progress[:3]
            base_avatar_path = "users/avatars/base_avatar.jpg"
            leaders = [
                {
                    "student_name": leader["student"].first_name,
                    "student_avatar": s3.get_link(leader["student"].profile.avatar.name)
                    if leader["student"].profile.avatar
                    else s3.get_link(base_avatar_path),
                    "progress_percent": leader["progress_percent"],
                }
                for leader in top_leaders
            ]

            # Добавляем прогресс и место в курсе в ответ
            course = {
                "course_id": course_obj.pk,
                "course_name": course_obj.name,
                "all_baselessons": all_base_lessons.count(),
                "completed_count": completed_all,
                "completed_percent": progress_percent,
                "average_mark": average_mark,
                "rank_in_course": student_rank,
                "top_leaders": leaders,
                "lessons": {
                    "completed_percent": self.calculate_progress(
                        completed_lessons.count(), all_lessons.count()
                    ),
                    "all_lessons": all_lessons.count(),
                    "completed_lessons": completed_lessons.count(),
                },
                "homeworks": {
                    "completed_percent": self.calculate_progress(
                        completed_homeworks.count(), all_homeworks.count()
                    ),
                    "all_homeworks": all_homeworks.count(),
                    "completed_homeworks": completed_homeworks.count(),
                },
                "tests": {
                    "completed_percent": self.calculate_progress(
                        completed_tests.count(), all_tests.count()
                    ),
                    "all_tests": all_tests.count(),
                    "completed_tests": completed_tests.count(),
                },
            }
            courses.append(course)

            if progress_percent == 100:
                student_history = StudentsHistory.objects.get(
                    user=student, students_group=student_group
                )
                if not student_history.finish_date:
                    student_history.finish_date = datetime.now()
                    student_history.save()

            CompletedCourseNotifications.send_completed_course_notification(
                progress_percent,
                student.id,
                course["course_id"],
                course["course_name"],
                school_id,
            )

        return Response(return_dict)

    def calculate_progress(self, completed_count, total_count):
        return round(completed_count / total_count * 100, 2) if total_count != 0 else 0

    def generate_progress(self, school_name, student, courses_ids):
        """Генерирует статистику по студенту по всем курсам в школе"""
        school_id = School.objects.get(name=school_name).school_id

        all_base_lesson_ids = UserProgressLogs.objects.filter(
            user=student.pk
        ).values_list("lesson_id", flat=True)

        return_dict = {}
        return_dict["student"] = student.email
        return_dict["school_id"] = school_id
        return_dict["school_name"] = school_name
        return_dict["courses"] = []

        for course_id in courses_ids:
            course = {}
            course_obj = Course.objects.get(pk=course_id)

            all_homeworks = Homework.objects.filter(section_id__course_id=course_id)

            completed_homeworks = all_homeworks.filter(
                baselesson_ptr_id__in=all_base_lesson_ids
            )

            course["course_id"] = course_obj.pk
            course["course_name"] = course_obj.name

            course["homeworks"] = {
                "completed_percent": round(
                    completed_homeworks.count() / all_homeworks.count() * 100, 2
                )
                if all_homeworks.count() != 0
                else 0,
                "all_homeworks": all_homeworks.count(),
                "completed_homeworks": completed_homeworks.count(),
            }

            return_dict["courses"].append(course)

        return Response(return_dict)

    def all_courses_progress_response(self, school_name, student, courses_ids):
        """Генерирует статистику по студенту по всем курсам в школе"""
        school_id = School.objects.get(name=school_name).school_id

        all_base_lesson_ids = UserProgressLogs.objects.filter(
            user=student.pk
        ).values_list("lesson_id", flat=True)

        return_dict = {}
        return_dict["student"] = student.email
        return_dict["school_id"] = school_id
        return_dict["school_name"] = school_name
        return_dict["courses"] = []

        for course_id in courses_ids:
            course = {}
            course_obj = Course.objects.get(pk=course_id)

            all_homeworks = Homework.objects.filter(section_id__course_id=course_id)

            completed_homeworks = all_homeworks.filter(
                baselesson_ptr_id__in=all_base_lesson_ids
            )

            course["course_id"] = course_obj.pk
            course["course_name"] = course_obj.name

            course["homeworks"] = {
                "completed_percent": round(
                    completed_homeworks.count() / all_homeworks.count() * 100, 2
                )
                if all_homeworks.count() != 0
                else 0,
                "all_homeworks": all_homeworks.count(),
                "completed_homeworks": completed_homeworks.count(),
            }

            return_dict["courses"].append(course)

        return Response(return_dict)
