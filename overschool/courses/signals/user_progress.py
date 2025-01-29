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
from django.core.cache import cache
from django.db.models import OuterRef
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone


@receiver([post_save, post_delete], sender=UserProgressLogs)
def update_progress(sender, instance, **kwargs):
    student_id = instance.user_id
    course_id = None

    # При удалении урока используем cached_lesson_course_id если он есть
    if hasattr(instance, "cached_lesson_course_id"):
        course_id = instance.cached_lesson_course_id
    else:
        # Безопасно проверяем существование связанных объектов
        try:
            if instance.lesson_id:
                lesson = instance.lesson
                if lesson.section and lesson.section.course:
                    course_id = lesson.section.course.course_id
        except BaseLesson.DoesNotExist:
            pass

    if course_id:
        cache_key = f"progress_update_{student_id}_{course_id}"
        # Проверим, когда последний раз обновлялся прогресс
        last_update = cache.get(cache_key)
        now = timezone.now()

        if (
            not last_update or (now - last_update).seconds > 180
        ):  # Обновляем, если прошло больше 3 минут
            progress = calculate_progress(student_id, course_id)
            StudentCourseProgress.objects.update_or_create(
                student_id=student_id,
                course_id=course_id,
                defaults={"progress": progress},
            )
            cache.set(cache_key, now, timeout=180)  # Устанавливаем таймаут на 3 минут
    else:
        pass


def calculate_progress(student_id, course_id):
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
    ).exclude(
        lessonavailability__student=student_id,
    )

    if all_base_lesson.count() == 0:
        return 0

    lesson_viewed_ids = UserProgressLogs.objects.filter(
        lesson_id__in=all_base_lesson.values("id"), user_id=student_id
    ).values_list("lesson_id", flat=True)

    lesson_completed_ids = UserProgressLogs.objects.filter(
        lesson_id__in=all_base_lesson.values("id"), completed=True, user_id=student_id
    ).values_list("lesson_id", flat=True)

    completed_lessons = (
        Lesson.objects.filter(section_id__course_id=course_id, active=True)
        .exclude(lessonavailability__student=student_id)
        .exclude(lessonenrollment__student_group=OuterRef("pk"))
        .filter(baselesson_ptr_id__in=lesson_viewed_ids)
        .count()
    )

    completed_homeworks = (
        Homework.objects.filter(section_id__course_id=course_id, active=True)
        .exclude(lessonavailability__student=student_id)
        .exclude(lessonenrollment__student_group=OuterRef("pk"))
        .filter(baselesson_ptr_id__in=lesson_completed_ids)
        .count()
    )

    completed_tests = (
        SectionTest.objects.filter(section_id__course_id=course_id, active=True)
        .exclude(lessonavailability__student=student_id)
        .exclude(lessonenrollment__student_group=OuterRef("pk"))
        .filter(baselesson_ptr_id__in=lesson_completed_ids)
        .count()
    )

    completed_all = completed_lessons + completed_homeworks + completed_tests
    return round((completed_all / all_base_lesson.count()) * 100, 2)
