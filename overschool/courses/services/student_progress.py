from courses.models import (
    BaseLesson,
    Course,
    Lesson,
    Homework,
    SectionTest,
    StudentsGroup,
    UserProgressLogs,
)
from django.db.models import Subquery


def get_student_progress(student, course_id):

    all_base_lesson = BaseLesson.objects.filter(
        section_id__course_id=course_id, active=True
    )

    lesson_viewed_ids = UserProgressLogs.objects.filter(
        lesson_id__in=all_base_lesson.values('id'),
        user_id=student).values_list("lesson_id",flat=True)

    lesson_completed_ids = UserProgressLogs.objects.filter(
        lesson_id__in=all_base_lesson.values('id'),
        completed=True,
        user_id=student).values_list("lesson_id", flat=True)


    all_lessons = Lesson.objects.filter(section_id__course_id=course_id, active=True)
    all_homeworks = Homework.objects.filter(section_id__course_id=course_id, active=True)
    all_tests = SectionTest.objects.filter(section_id__course_id=course_id, active=True)

    completed_lessons = all_lessons.filter(
        baselesson_ptr_id__in=lesson_viewed_ids
    )

    completed_homeworks = all_homeworks.filter(
        baselesson_ptr_id__in=lesson_completed_ids
    )

    completed_tests = all_tests.filter(
        baselesson_ptr_id__in=lesson_completed_ids
    )
    completed_all = completed_lessons.count() + completed_homeworks.count() + completed_tests.count()

    progress_percent = round(
            completed_all / all_base_lesson.count() * 100, 2) if all_base_lesson.count() != 0 else 0

    return progress_percent
