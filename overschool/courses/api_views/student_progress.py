from datetime import datetime

from common_services.selectel_client import UploadToS3
from courses.api_views.schemas import StudentProgressSchemas
from courses.models import (
    BaseLesson,
    Course,
    CourseCopy,
    Lesson,
    LessonAvailability,
    LessonEnrollment,
    SectionTest,
    StudentCourseProgress,
    StudentsGroup,
    StudentsHistory,
    UserHomework,
    UserProgressLogs,
)
from courses.models.homework.homework import Homework
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, F, Q, Window
from django.db.models.functions import Rank, RowNumber
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
        course_id = request.query_params.get("course_id", None)
        school_id = School.objects.get(name=school_name).school_id

        is_student = StudentsGroup.objects.filter(
            students=user,
            course_id__school__school_id=school_id,
        ).exists()

        if (
            not is_student
            and not user.groups.filter(group__name="Admin", school=school_id).exists()
        ):
            return Response(
                f"Студент не найден в школе {school_name}.",
                status=status.HTTP_403_FORBIDDEN,
            )

        if not course_id:
            courses_ids = StudentsGroup.objects.filter(
                students=user, course_id__school__school_id=school_id
            ).values_list("course_id", flat=True)
            return self.generate_all_response(
                student=user, school_name=school_name, courses_ids=courses_ids
            )
        else:
            courses_ids = [int(course_id)]

        return self.generate_response(
            student=user, school_name=school_name, courses_ids=courses_ids
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

    def generate_all_response(self, school_name, student, courses_ids):
        """Генерирует статистику по студенту по всем курсам в школе (с исправленным подсчетом)"""
        try:

            school = School.objects.get(name=school_name)
        except School.DoesNotExist:
            return Response(
                {"error": f"Школа {school_name} не найдена"},
                status=status.HTTP_404_NOT_FOUND,
            )

        courses_data = []

        courses = {c.pk: c for c in Course.objects.filter(pk__in=courses_ids)}

        student_groups = {
            sg.course_id_id: sg
            for sg in StudentsGroup.objects.filter(
                students=student, course_id__in=courses_ids
            )
        }

        for course_pk in courses_ids:
            course = courses.get(course_pk)
            if not course:

                print(f"Предупреждение: Курс с ID {course_pk} не найден.")
                continue

            student_group = student_groups.get(course_pk)

            query_course_id = course_pk
            if course.is_copy:

                original_course_id = (
                    CourseCopy.objects.filter(course_copy_id=course.pk)
                    .values_list("course_id", flat=True)
                    .first()
                )
                if original_course_id:
                    query_course_id = original_course_id

            # 1. Получаем ID активных уроков в курсе
            active_lesson_ids = set(
                BaseLesson.objects.filter(
                    section__course_id=query_course_id, active=True
                ).values_list("id", flat=True)
            )

            # 2. Получаем ID уроков, доступных этому студенту через LessonAvailability
            available_via_enrollment_ids = set(
                LessonAvailability.objects.filter(
                    lesson__section__course_id=query_course_id,
                    student=student,
                    available=True,
                ).values_list("lesson_id", flat=True)
            )

            # 3. Объединяем ID - это все уроки, потенциально доступные студенту
            potentially_available_lesson_ids = (
                active_lesson_ids | available_via_enrollment_ids
            )

            # 4. Применяем исключения LessonEnrollment, если есть группа
            excluded_lesson_ids = set()
            if student_group:
                excluded_lesson_ids = set(
                    LessonEnrollment.objects.filter(
                        student_group=student_group,
                        lesson_id__in=potentially_available_lesson_ids,
                    ).values_list("lesson_id", flat=True)
                )

            # 5. Финальный набор ID уроков, которые должны учитываться в статистике
            final_lesson_ids = potentially_available_lesson_ids - excluded_lesson_ids

            if not final_lesson_ids:

                course_data = {
                    "course_id": course.pk,
                    "course_name": course.name,
                    "all_baselessons": 0,
                    "completed_count": 0,
                    "completed_percent": 0.0,
                    "average_mark": 0,
                    "lessons": self.get_lesson_stats_zero(),
                    "homeworks": self.get_lesson_stats_zero(),
                    "tests": self.get_lesson_stats_zero(),
                }
                courses_data.append(course_data)
                continue

            # 6. Получаем логи прогресса для этих уроков и студента
            progress_logs = UserProgressLogs.objects.filter(
                lesson_id__in=final_lesson_ids, user=student
            )

            viewed_lesson_ids = set(progress_logs.values_list("lesson_id", flat=True))
            completed_lesson_ids = set(
                progress_logs.filter(completed=True).values_list("lesson_id", flat=True)
            )

            # 7. Фильтруем конкретные типы уроков по финальному набору ID
            all_lessons_final_qs = Lesson.objects.filter(
                baselesson_ptr_id__in=final_lesson_ids
            )
            all_homeworks_final_qs = Homework.objects.filter(
                baselesson_ptr_id__in=final_lesson_ids
            )
            all_tests_final_qs = SectionTest.objects.filter(
                baselesson_ptr_id__in=final_lesson_ids
            )

            # 8. Считаем количество уроков КАЖДОГО типа из финального набора
            count_all_lessons = all_lessons_final_qs.count()
            count_all_homeworks = all_homeworks_final_qs.count()
            count_all_tests = all_tests_final_qs.count()

            total_lessons_final = len(final_lesson_ids)

            # 9. Считаем завершенные уроки КАЖДОГО типа

            completed_lessons_count = all_lessons_final_qs.filter(
                baselesson_ptr_id__in=viewed_lesson_ids
            ).count()
            completed_homeworks_count = all_homeworks_final_qs.filter(
                baselesson_ptr_id__in=completed_lesson_ids
            ).count()
            completed_tests_count = all_tests_final_qs.filter(
                baselesson_ptr_id__in=completed_lesson_ids
            ).count()

            total_completed_final = (
                completed_lessons_count
                + completed_homeworks_count
                + completed_tests_count
            )

            # 10. Считаем прогресс
            progress_percent = self.calculate_progress(
                total_completed_final, total_lessons_final
            )

            # 11. Считаем среднюю оценку (запрос можно оптимизировать, если делать его вне цикла)
            homework_ids_for_avg = all_homeworks_final_qs.values_list(
                "baselesson_ptr_id", flat=True
            )
            average_mark = (
                UserHomework.objects.filter(
                    user=student, homework_id__in=homework_ids_for_avg
                ).aggregate(average_mark=Avg("mark"))["average_mark"]
                or 0
            )
            average_mark = round(average_mark, 2)

            course_data = {
                "course_id": course.pk,
                "course_name": course.name,
                "all_baselessons": total_lessons_final,
                "completed_count": total_completed_final,
                "completed_percent": progress_percent,
                "average_mark": average_mark,
                "lessons": self.get_lesson_stats(
                    count_all_lessons, completed_lessons_count
                ),
                "homeworks": self.get_lesson_stats(
                    count_all_homeworks, completed_homeworks_count
                ),
                "tests": self.get_lesson_stats(count_all_tests, completed_tests_count),
            }
            courses_data.append(course_data)

            if progress_percent == 100:
                self.update_student_history(student, student_group)

            CompletedCourseNotifications.send_completed_course_notification(
                progress_percent, student.id, course.pk, course.name, school.school_id
            )

        return Response(
            {
                "student": student.email,
                "school_id": school.school_id,
                "school_name": school_name,
                "courses": courses_data,
            }
        )

    def generate_response(self, school_name, student, courses_ids):
        """Генерирует статистику по студенту по всем курсам в школе"""
        school = School.objects.get(name=school_name)
        courses_data = []
        base_query = Q(active=True) | Q(lessonavailability__available=True)
        for course_id in courses_ids:
            course = Course.objects.get(pk=course_id)
            student_group = StudentsGroup.objects.filter(
                students=student, course_id=course
            ).first()

            if course.is_copy:
                course_id = (
                    CourseCopy.objects.filter(course_copy_id=course.course_id)
                    .values_list("course_id", flat=True)
                    .first()
                    or course_id
                )

            base_lessons = BaseLesson.objects.filter(
                section__course_id=course_id
            ).filter(base_query)

            progress_logs = UserProgressLogs.objects.filter(
                lesson__in=base_lessons, user=student
            )
            viewed_lessons = progress_logs.values_list("lesson_id", flat=True)
            completed_lessons = progress_logs.filter(completed=True).values_list(
                "lesson_id", flat=True
            )

            all_lessons = Lesson.objects.filter(section__course_id=course_id).filter(
                base_query
            )
            all_homeworks = Homework.objects.filter(
                section__course_id=course_id
            ).filter(base_query)
            all_tests = SectionTest.objects.filter(section__course_id=course_id).filter(
                base_query
            )

            if student_group:
                exclude_query = Q(lessonenrollment__student_group=student_group)
                all_lessons = all_lessons.exclude(exclude_query)
                all_homeworks = all_homeworks.exclude(exclude_query)
                all_tests = all_tests.exclude(exclude_query)

            completed_counts = {
                "lessons": all_lessons.filter(
                    baselesson_ptr_id__in=viewed_lessons
                ).count(),
                "homeworks": all_homeworks.filter(
                    baselesson_ptr_id__in=completed_lessons
                ).count(),
                "tests": all_tests.filter(
                    baselesson_ptr_id__in=completed_lessons
                ).count(),
            }

            total_completed = sum(completed_counts.values())
            total_lessons = base_lessons.count()

            progress_percent = self.calculate_progress(total_completed, total_lessons)

            average_mark = (
                UserHomework.objects.filter(
                    user=student, homework__section__course_id=course_id
                ).aggregate(average_mark=Avg("mark"))["average_mark"]
                or 0
            )

            (
                current_student_rank,
                top_3_leaders,
                better_than_percent,
            ) = self.get_students_progress(course.pk, student)

            course_data = {
                "course_id": course.pk,
                "course_name": course.name,
                "all_baselessons": total_lessons,
                "completed_count": total_completed,
                "completed_percent": progress_percent,
                "average_mark": average_mark,
                "better_than_percent": better_than_percent,
                "rank_in_course": current_student_rank,
                "top_leaders": top_3_leaders,
                "lessons": self.get_lesson_stats(
                    all_lessons, completed_counts["lessons"]
                ),
                "homeworks": self.get_lesson_stats(
                    all_homeworks, completed_counts["homeworks"]
                ),
                "tests": self.get_lesson_stats(all_tests, completed_counts["tests"]),
            }

            courses_data.append(course_data)

            if progress_percent == 100:
                self.update_student_history(student, student_group)

            CompletedCourseNotifications.send_completed_course_notification(
                progress_percent, student.id, course.pk, course.name, school.school_id
            )

        return Response(
            {
                "student": student.email,
                "school_id": school.school_id,
                "school_name": school_name,
                "courses": courses_data,
            }
        )

    def get_students_progress(self, course_id, current_student):

        progress_for_students = (
            StudentCourseProgress.objects.filter(progress__gt=0, course_id=course_id)
            .select_related("student", "student__profile")
            .annotate(
                rank=Window(
                    expression=RowNumber(),
                    order_by=[F("progress").desc(), F("last_updated").asc()],
                )
            )
        )

        base_avatar_path = "users/avatars/base_avatar.jpg"

        # Получаем всё одним запросом
        results = list(
            progress_for_students.values(
                "student_id",
                "student__first_name",
                "student__profile__avatar",
                "progress",
                "rank",
            )
        )

        # Получаем место текущего студента
        current_student_progress = next(
            (entry for entry in results if entry["student_id"] == current_student.id),
            None,
        )

        current_student_rank = (
            current_student_progress["rank"] if current_student_progress else None
        )

        # **Рассчитываем, насколько студент лучше других (в процентах)**
        better_than_percent = (
            100 if len(results) == 1 else 0
        )  # Если он единственный, то 100%
        if results and current_student_progress and len(results) > 1:
            lower_progress_count = sum(
                1
                for r in results
                if r["progress"] < current_student_progress["progress"]
            )
            better_than_percent = round(
                (lower_progress_count / (len(results) - 1)) * 100
            )

        # Форматируем лидеров
        top_3_leaders = [
            {
                "student_name": result["student__first_name"],
                "student_avatar": s3.get_link(result["student__profile__avatar"])
                if result["student__profile__avatar"]
                else s3.get_link(base_avatar_path),
                "progress_percent": result["progress"],
            }
            for result in results[:3]
        ]

        return current_student_rank, top_3_leaders, better_than_percent

    def get_top_leaders(self, top_students):
        base_avatar_path = "users/avatars/base_avatar.jpg"
        return [
            {
                "student_name": leader["student"].first_name,
                "student_avatar": s3.get_link(leader["student"].profile.avatar.name)
                if leader["student"].profile.avatar
                else s3.get_link(base_avatar_path),
                "progress_percent": leader["progress_percent"],
            }
            for leader in top_students
        ]

    def get_lesson_stats(self, all_items_count, completed_items_count):
        """Обновленная функция для статистики по типу урока"""
        return {
            "completed_percent": self.calculate_progress(
                completed_items_count, all_items_count
            ),
            "all_lessons": all_items_count,
            "completed_lessons": completed_items_count,
        }

    def get_lesson_stats_zero(self):
        """Возвращает нулевую статистику, если уроков нет"""
        return {
            "completed_percent": 0.0,
            "all_lessons": 0,
            "completed_lessons": 0,
        }

    def update_student_history(self, student, student_group):
        student_history, created = StudentsHistory.objects.get_or_create(
            user=student,
            students_group=student_group,
            defaults={"finish_date": datetime.now()},
        )
        if not created and not student_history.finish_date:
            student_history.finish_date = datetime.now()
            student_history.save()

    def calculate_progress(self, completed_count, total_count):
        return round(completed_count / total_count * 100, 2) if total_count > 0 else 0.0

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
