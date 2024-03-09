from courses.models import (
    BaseLesson,
    Course,
    Homework,
    Lesson,
    SectionTest,
    StudentsGroup,
    UserProgressLogs,
)
from courses.models.common.base_lesson import LessonAvailability, LessonEnrollment
from django.db.models import Prefetch

# Прогресс для таблиц ********************************


def get_student_progress(student, course_id, group_id):
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
