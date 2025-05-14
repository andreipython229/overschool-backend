from courses.models import (
    BaseLesson,
    Course,
    CourseCopy,
    Homework,
    Lesson,
    SectionTest,
    StudentCourseProgress,
    StudentsGroup,
    UserProgressLogs,
)
from courses.models.common.base_lesson import LessonAvailability, LessonEnrollment
from django.db.models import (
    ExpressionWrapper,
    FloatField,
    OuterRef,
    Prefetch,
    Subquery,
    Value,
)

# Прогресс для таблиц ********************************


def get_student_progress(student, course_id, group_id):
    try:
        course = Course.objects.get(course_id=course_id)
        if course.is_copy:
            course_copy = CourseCopy.objects.get(course_copy_id=course_id)
            course_id = course_copy.course_id
    except Course.DoesNotExist:
        return 0

    all_base_lesson = BaseLesson.objects.filter(
        section_id__course_id=course_id,
        active=True,
    ).prefetch_related(
        Prefetch(
            "lessonavailability_set",
            queryset=LessonAvailability.objects.exclude(student=student),
        ),
        Prefetch(
            "lessonenrollment_set",
            queryset=LessonEnrollment.objects.exclude(student_group=group_id),
        ),
    )

    user_progress_logs = UserProgressLogs.objects.filter(
        lesson_id__in=all_base_lesson.values_list("id", flat=True),
        user_id=student,
    ).values_list("lesson_id", "completed")

    lesson_viewed_ids = [log[0] for log in user_progress_logs]
    lesson_completed_ids = [log[0] for log in user_progress_logs if log[1]]

    all_lessons = Lesson.objects.filter(baselesson_ptr_id__in=all_base_lesson)
    all_homeworks = Homework.objects.filter(baselesson_ptr_id__in=all_base_lesson)
    all_tests = SectionTest.objects.filter(baselesson_ptr_id__in=all_base_lesson)

    completed_lessons = all_lessons.filter(baselesson_ptr_id__in=lesson_viewed_ids)
    completed_homeworks = all_homeworks.filter(
        baselesson_ptr_id__in=lesson_completed_ids
    )
    completed_tests = all_tests.filter(baselesson_ptr_id__in=lesson_completed_ids)

    completed_all = (
        completed_lessons.count()
        + completed_homeworks.count()
        + completed_tests.count()
    )
    progress_percent = (
        round(completed_all / all_base_lesson.count() * 100)
        if all_base_lesson.count() != 0
        else 0
    )

    return progress_percent


def progress_subquery(student_id, course_id):
    try:
        course = Course.objects.get(course_id=course_id)
        if course.is_copy:
            try:
                course_copy = CourseCopy.objects.get(course_copy_id=course_id)
                course_id = course_copy.course_id
            except CourseCopy.DoesNotExist:
                pass

        # Получаем сохранённый прогресс
        progress = StudentCourseProgress.objects.get(
            student_id=student_id, course_id=course_id
        ).progress
        return progress
    except (Course.DoesNotExist, StudentCourseProgress.DoesNotExist):
        return 0
