from django.db import models
from users.models import User

from ..homework.homework import Homework
from ..lesson.lesson import Lesson
from ..test.section_test import SectionTest


class UserLessonSettings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    show_lesson = models.BooleanField(default=True, verbose_name="Отображать урок")

    class Meta:
        unique_together = ("user", "lesson")


class UserHomeworkSettings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE)
    show_homework = models.BooleanField(default=True, verbose_name="Отображать домашнее задание")

    class Meta:
        unique_together = ("user", "homework")


class UserTestSettings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    test = models.ForeignKey(SectionTest, on_delete=models.CASCADE)
    show_test = models.BooleanField(default=True, verbose_name="Отображать тест")

    class Meta:
        unique_together = ("user", "test")
