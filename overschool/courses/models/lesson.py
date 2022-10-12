from courses.managers import LessonManager

from .base_lesson import BaseLesson


## TODO: как загружать бесконечное количество медиа в урок или тест, или дз
class Lesson(BaseLesson):
    """Модель урока в разделе"""

    objects = LessonManager()

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
