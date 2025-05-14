from urllib.parse import unquote, urlparse

from ckeditor.fields import RichTextField
from common_services.mixins import TimeStampMixin, VisibilityMixin, PositionMixin
from common_services.services import TruncateFileName, limit_image_size
from django.db import models
from courses.models import Course


class HeaderBlock(PositionMixin, VisibilityMixin, models.Model):
    """Модель шапки лендинга"""

    id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID",
        help_text="Уникальный идентификатор блока шапки курса",
    )

    def __str__(self):
        return f"{self.id}"

    class Meta:
        verbose_name = "Блок с шапкой"
        verbose_name_plural = "Блоки с шапкой"


class StatsBlock(PositionMixin, VisibilityMixin, models.Model):
    """Модель блока статистики курса"""

    id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID",
        help_text="Уникальный идентификатор блока статистики курса",
    )

    def __str__(self):
        return f"{self.id}"

    class Meta:
        verbose_name = "Блок со статистикой"
        verbose_name_plural = "Блоки со статистикой"


class BlockCards(models.Model):
    """Модель карточек блока"""
    """   *** ФОТО ***   """
    """ *** НАЗВАНИЕ *** """
    """ *** ОПИСАНИЕ *** """

    id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID",
        help_text="Уникальный идентификатор блока статистики курса",
    )

    position = models.IntegerField(
        verbose_name="Позиция в порядке следования карточек",
        help_text="Номер следования в списке карточек",
        default=0,
    )

    photo = models.ImageField(
        verbose_name="Фотография",
        help_text="Фотография для карточки",
        max_length=300,
        validators=[limit_image_size],
        upload_to=TruncateFileName(300),
        blank=True,
        null=True,
    )
    title = RichTextField(
        max_length=256,
        verbose_name="Название карточки",
        help_text="Название карточки",
        blank=True,
        null=True,
    )
    description = RichTextField(
        max_length=256,
        verbose_name="Описание карточки",
        help_text="Описание карточки",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.id}"

    class Meta:
        verbose_name = "Карточка блока"
        verbose_name_plural = "Карточки блока"


class AudienceBlock(PositionMixin, VisibilityMixin, models.Model):
    """Модель блока целевой аудитории курса"""

    id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID",
        help_text="Уникальный идентификатор блока целевая аудитория курса",
    )
    description = RichTextField(
        max_length=256,
        verbose_name="Описание блока",
        help_text="Описание блока",
        blank=True,
        null=True,
    )
    chips = models.ManyToManyField(
        BlockCards,
        verbose_name="Блок карточек",
    )

    def __str__(self):
        return f"{self.id}"

    class Meta:
        verbose_name = "Блок с целевой аудиторией"
        verbose_name_plural = "Блоки с целевой аудиторией"


class TrainingProgram(PositionMixin, VisibilityMixin, models.Model):
    """Модель блока программы обучения"""

    id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID",
        help_text="Уникальный идентификатор блока программа обучения курса",
    )

    def __str__(self):
        return f"{self.id}"

    class Meta:
        verbose_name = "Блок с программой обучения"
        verbose_name_plural = "Блоки с программой обучения"


class TrainingPurpose(PositionMixin, VisibilityMixin, models.Model):
    """Модель блока цель обучения"""

    id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID",
        help_text="Уникальный идентификатор блока цели обучения",
    )
    description = RichTextField(
        max_length=256,
        verbose_name="Описание блока",
        help_text="Описание блока",
        blank=True,
        null=True,
    )
    chips = models.ManyToManyField(
        BlockCards,
        verbose_name="Блок карточек",
    )

    def __str__(self):
        return f"{self.id}"

    class Meta:
        verbose_name = "Блок с целью обучения обучения"
        verbose_name_plural = "Блоки с целью обучения обучения"


class LinkButton(PositionMixin, VisibilityMixin, models.Model):
    """Кнопки со ссылками для редактора лендинга"""
    id = models.AutoField(primary_key=True,
                          editable=False,
                          verbose_name='ID',
                          help_text='Уникальный идентификатор блока цели обучения')

    name = models.CharField(
        max_length=200,
        verbose_name="Текст кнопки",
        help_text="Текст кнопки",
    )
    link = models.URLField(
        max_length=500,
        verbose_name="Ссылка",
        help_text="Ссылка для перехода по кнопке",
        blank=True,
        null=True,
    )
    color = models.CharField(
        max_length=50,
        verbose_name="Цвет кнопки",
        help_text="Цвет кнопки",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Кнопка со ссылками для редактора лендинга"
        verbose_name_plural = "Кнопки со ссылками для редактора лендинга"


class CourseLanding(models.Model):
    """Модель лендинга курса"""

    id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID",
        help_text="Уникальный идентификатор лендинга курса",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="course_school",
        verbose_name="ID школы",
        help_text="ID школы",
    )
    header = models.ForeignKey(
        HeaderBlock,
        on_delete=models.CASCADE,
        related_name="header_block",
        verbose_name="Шапка лендинга",
        help_text="Верхний блок с коротким описанием курса и изображением",
    )
    stats = models.ForeignKey(
        StatsBlock,
        on_delete=models.CASCADE,
        related_name="stats_block",
        verbose_name="Статистика",
        help_text="Блок со статистикой курса",
    )
    audience = models.ForeignKey(
        AudienceBlock,
        on_delete=models.CASCADE,
        related_name="audience_block",
        verbose_name="Целевая аудитория",
        help_text="Блок с целевой аудиторией",
    )
    training_program = models.ForeignKey(
        TrainingProgram,
        on_delete=models.CASCADE,
        related_name="training_program_block",
        verbose_name="Программа обучения",
        help_text="Блок с программой обучения курса",
    )
    training_purpose = models.ForeignKey(
        TrainingPurpose,
        on_delete=models.CASCADE,
        related_name="training_purpose_block",
        verbose_name="Цель обучения",
        help_text="Блок с целью обучения курсу",
    )
    link_button = models.ForeignKey(LinkButton, on_delete=models.CASCADE, related_name="link_button",
                                    verbose_name="Кнопка с ссылкой", help_text="Блок с ссылками", null=True)

    def __str__(self):
        return f"[{self.id}] {self.course.name}"

    class Meta:
        verbose_name = "Блок с лендингом курса"
        verbose_name_plural = "Блоки с лендингом курсов"
