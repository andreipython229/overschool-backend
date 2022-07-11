from ckeditor.fields import RichTextField
from django.db import models
from .time_stamped_model import TimeStampedModel


class Status(models.TextChoices):
    "Варианты статусов для курса"
    UNPUBLISHED = 'НО', 'Не опубликован'
    PUBLISHED = 'О', 'Опубликован'


class Course(TimeStampedModel):
    "Модель курсов"
    course_id = models.AutoField(primary_key=True, editable=False,
                                 verbose_name="Курс ID",
                                 help_text="Уникальный идентификатор курса")
    name = models.CharField(max_length=256, verbose_name="Название курса",
                            help_text="Главное название курса")
    duration_days = models.IntegerField(verbose_name="Продолжительность курса",
                                        help_text="Продолжительность курса в днях")
    status = models.CharField(max_length=256,
                              choices=Status.choices,
                              default=Status.UNPUBLISHED,
                              verbose_name="Статус курса",
                              help_text="Статус курса, отображает состояние курса (опубликован - то сть используется юзерами, не опубликован - это ещё в разработке")
    price = models.DecimalField(max_digits=15, decimal_places=2,
                                verbose_name="Цена",
                                help_text="Цена курса в BYN")
    description = RichTextField(verbose_name="Описание",
                                help_text="Описание курса для отображения, сохраняется в html")
    photo = models.ImageField(upload_to="images/courses/main/", verbose_name="Фотография",
                              help_text="Главная фотография")

    def __str__(self):
        return str(self.course_id)+" "+str(self.name)

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"

