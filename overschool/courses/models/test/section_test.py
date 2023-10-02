from django.db import models
from model_clone import CloneMixin

from ..common.base_lesson import BaseLesson


class SectionTest(BaseLesson, CloneMixin):
    """Модель теста"""

    test_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID теста",
        help_text="Уникальный идентификатор теста",
    )
    random_test_generator = models.BooleanField(
        default=False,
        verbose_name="Автотест",
        help_text="Автоматическая генерация теста",
    )
    num_questions = models.IntegerField(
        default=0,
        verbose_name="Количество вопросов",
        help_text="Количество вопросов для генерации теста",
    )
    success_percent = models.IntegerField(
        default=0,
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
    _clone_m2o_or_o2m_fields = ["questions"]

    class Meta:
        verbose_name = "Тест"
        verbose_name_plural = "Тесты"
        default_related_name = "tests"


class RandomTestTests(models.Model):
    test = models.ForeignKey(SectionTest, related_name="test", on_delete=models.CASCADE)
    target_test = models.ForeignKey(
        SectionTest, related_name="target_test", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = "Тесты для генерации"
        verbose_name_plural = "Тесты для генерации"
