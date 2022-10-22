from django.db import models
from model_clone import CloneMixin

from ..common.base_lesson import BaseLesson


class SectionTest(BaseLesson, CloneMixin):
    """Модель теста"""

    success_percent = models.IntegerField(
        verbose_name="Проходной балл",
        help_text="Процент правильных ответов для успешно пройденного теста",
    )
    random_questions = models.BooleanField(
        default=False, verbose_name="Перемешать вопросы"
    )
    random_answers = models.BooleanField(
        default=False, verbose_name="Перемешать ответы"
    )
    show_right_answers = models.BooleanField(
        default=False, verbose_name="Показать правильные ответы"
    )
    attempt_limit = models.BooleanField(
        default=False, verbose_name="Ограничить количество попыток"
    )
    attempt_count = models.PositiveIntegerField(
        default=0, verbose_name="Кол-во попыток (если 0, то бесконечно)"
    )
    points_per_answer = models.PositiveIntegerField(
        default=1, verbose_name="Бал за каждый правильный ответ"
    )
    _clone_m2o_or_o2m_fields = ["question_test_id_fk"]

    class Meta:
        verbose_name = "Тест"
        verbose_name_plural = "Тесты"
