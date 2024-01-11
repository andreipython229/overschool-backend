from ckeditor.fields import RichTextField
from common_services.mixins import AuthorMixin, OrderMixin, TimeStampMixin
from common_services.services import TruncateFileName
from django.db import connection, models
from model_clone import CloneMixin
from users.models import User

from ..courses.section import Section
from ..students.students_group import StudentsGroup


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
    _clone_m2o_or_o2m_fields = ["text_files", "audio_files", "url"]

    def __str__(self):
        return f"{self.section}. {self.name}"

    def is_available_for_student(self, student):
        try:
            availability = LessonAvailability.objects.get(student=student, lesson=self)
            return availability.available
        except LessonAvailability.DoesNotExist:
            return None

    def save(self, *args, **kwargs):
        if not self.order:
            max_order = BaseLesson.objects.all().aggregate(models.Max("order"))[
                "order__max"
            ]
            order = max_order + 1 if max_order is not None else 1
            self.order = order
        if self.__class__ is not BaseLesson:
            if self.baselesson_ptr_id:
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
                # Проверяем наличие ограничения
                cursor.execute(
                    f"SELECT constraint_name FROM information_schema.constraint_column_usage WHERE table_name = %s AND constraint_name = %s;",
                    (cls._meta.db_table, constraint_name),
                )
                if cursor.fetchone():
                    # Ограничение существует, отключаем его
                    cursor.execute(
                        f"ALTER TABLE {cls._meta.db_table} DROP CONSTRAINT {constraint_name};"
                    )
                    return True
                else:
                    # Ограничение не существует
                    return False
        except Exception as e:
            # Обработка ошибок
            print(f"Error: {e}")
            return False

    @classmethod
    def enable_constraint(cls):
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
                    'ALTER TABLE courses_baselesson ADD CONSTRAINT unique_section_lesson_order UNIQUE (section_id, "order");'
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


class BlockType(models.TextChoices):
    VIDEO = "video", "video"
    PICTURE = "picture", "picture"
    DESCRIPTION = "description", "description"
    CODE = "code", "code"


class BaseLessonBlock(OrderMixin, models.Model):
    """Блоки урока"""

    base_lesson = models.ForeignKey(
        BaseLesson, on_delete=models.CASCADE, related_name="blocks"
    )
    video = models.FileField(
        verbose_name="Видео",
        help_text="Видеофайл размером до 2 ГБ",
        max_length=300,
        upload_to=TruncateFileName(300),
        blank=True,
        null=True,
    )
    url = models.URLField(
        verbose_name="URL видео",
        help_text="Ссылка на видео из YouTube",
        blank=True,
        null=True,
    )
    description = RichTextField(
        verbose_name="Описание",
        help_text="Описание к уроку",
        blank=True,
        null=True,
    )
    code = RichTextField(
        verbose_name="Код",
        help_text="Примеры кода к уроку",
        blank=True,
        null=True,
    )
    picture = models.ImageField(
        verbose_name="Картинка",
        help_text="Картинка к уроку",
        upload_to=TruncateFileName(300),
        blank=True,
        null=True,
    )
    type = models.CharField(
        max_length=15,
        choices=BlockType.choices,
        default=BlockType.DESCRIPTION,
        verbose_name="Тип блока",
        help_text="Тип блока",
    )

    class Meta:
        verbose_name = "Блок урока"
        verbose_name_plural = "Блоки уроков"


class LessonAvailability(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="lesson_availability",
        verbose_name="Студент",
    )
    lesson = models.ForeignKey(
        BaseLesson, on_delete=models.CASCADE, verbose_name="Урок/ДЗ/Тест"
    )
    available = models.BooleanField(default=False, verbose_name="Доступен")

    class Meta:
        verbose_name = "Доступность урока для студента"
        verbose_name_plural = "Доступность уроков для студентов"


class LessonEnrollment(models.Model):
    student_group = models.ForeignKey(
        StudentsGroup,
        on_delete=models.CASCADE,
        related_name="lesson_enrollment",
        verbose_name="Группа студента",
    )
    lesson = models.ForeignKey(
        BaseLesson, on_delete=models.CASCADE, verbose_name="Урок/ДЗ/Тест"
    )

    class Meta:
        verbose_name = "Доступность урока для группы"
        verbose_name_plural = "Доступность урока для группы"
