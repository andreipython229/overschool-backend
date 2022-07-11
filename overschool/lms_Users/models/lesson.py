from django.db import models
from embed_video.fields import EmbedVideoField

from lms_Users.database_managers.lesson import LessonManager
from .time_stamped_model import TimeStampedModel


# Надо добавить очередь
class Lesson(TimeStampedModel):
    "Модель урока в разделе"
    lesson_id = models.AutoField(primary_key=True, editable=False,
                                 verbose_name="ID Урока",
                                 help_text="Уникальный идентификатор урока")
    section_id = models.ForeignKey(Section, on_delete=models.CASCADE,
                                   related_name="section_lesson_id_fk",
                                   verbose_name="ID раздела",
                                   help_text="ID раздела курса")
    name = models.CharField(max_length=256, verbose_name="Название урока",
                            help_text="Название урока")
    description = models.TextField(verbose_name="Описание",
                                   help_text="Описание к уроку")
    video = EmbedVideoField(verbose_name="Видео",
                            help_text="Сюда всталвяем ссылку на видос с ютуба, поэтому сначала его надо загрузить туда")
    previous_lesson_id = models.ForeignKey('self', on_delete=models.PROTECT,
                                           related_name="lesson_id_fk",
                                           verbose_name="Предыдущий урок",
                                           help_text="Предыдущий урок, если None, значит, этот урок первый",
                                           null=True)

    objects = LessonManager

    def __str__(self):
        return str(self.lesson_id)+" "+str(self.name)

    def order(self):
        if self.previous_lesson_id:
            previous_lesson: Lesson = Lesson.objects.get(lesson_id=self.previous_lesson_id)
            return previous_lesson.order() + 1
        else:
            return 0

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
