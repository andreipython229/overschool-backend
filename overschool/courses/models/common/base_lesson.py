from ckeditor.fields import RichTextField
from common_services.mixins import AuthorMixin, OrderMixin, TimeStampMixin
from django.db import connection, models
from model_clone import CloneMixin

from ..courses.section import Section


class BaseLesson(TimeStampMixin, AuthorMixin, OrderMixin, CloneMixin, models.Model):
    """Базовая модель урока в разделе"""

    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="ID раздела",
        help_text="ID раздела курса",
    )
    name = models.CharField(
        max_length=256,
        verbose_name="Название урока",
        help_text="Название урока",
        default="Имя не придумано",
    )
    description = RichTextField(
        verbose_name="Описание", help_text="Описание к уроку", blank=True, null=True
    )
    code = RichTextField(
        verbose_name="Код", help_text="Примеры кода к уроку", blank=True, null=True
    )
    video = models.FileField(
        verbose_name="Видео",
        help_text="Видеофайл размером до 2 ГБ",
        blank=True,
        null=True,
    )
    points = models.PositiveIntegerField(
        verbose_name="Баллы за прохождение",
        help_text="Баллы за прохождение",
        default=0,
    )
    active = models.BooleanField(
        default=False,
        verbose_name="Активный",
        help_text="Определяет, виден ли урок, домашнее задание или тест всем кроме админа",
        blank=False,
    )
    _clone_o2o_fields = ["lessons", "homeworks", "tests"]
    _clone_m2o_or_o2m_fields = ["text_files", "audio_files"]

    def __str__(self):
        return f"{self.section}. {self.name}"

    def save(self, *args, **kwargs):
        if self.__class__ is not BaseLesson:
            baselesson = BaseLesson.objects.get(pk=self.baselesson_ptr_id)
            self.section_id = baselesson.section.pk

        super().save(*args, **kwargs)

    @classmethod
    def disable_constraint(cls, constraint_name):
        """
        Метод для отключения ограничения базы данных.

        Args:
            constraint_name (str): Название ограничения для отключения.

        Returns:
            bool: True, если ограничение успешно отключено, иначе False.
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"ALTER TABLE {cls._meta.db_table} DROP CONSTRAINT {constraint_name};"
                )
            return True
        except Exception as e:
            return False

    @classmethod
    def enable_constraint(cls, constraint_name):
        """
        Метод для включения ограничения базы данных.

        Args:
            constraint_name (str): Название ограничения для включения.

        Returns:
            bool: True, если ограничение успешно включено, иначе False.
        """

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"ALTER TABLE {cls._meta.db_table} ADD CONSTRAINT {constraint_name};"
                )
            return True
        except Exception as e:
            return False

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["section", "order"], name="unique_section_lesson_order"
            ),
        ]
