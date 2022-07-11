from django.db import models

from .time_stamped_model import TimeStampedModel
from .test import Test
from .user import User


class UserTestStatusChoices(models.TextChoices):
    "Варианты статусов для пройденного теста"
    SUCCESS = 'П', 'Прошёл'
    FAILED = 'Н', 'Не прошёл'


class UserTest(TimeStampedModel):
    "Модель сданнаго теста учеником"
    user_test_id = models.AutoField(primary_key=True, editable=False,
                                    verbose_name="ID сданнаго теста",
                                    help_text="Уникальный идентификатор сданнаго теста")
    test_id = models.ForeignKey(Test, on_delete=models.CASCADE,
                                verbose_name="ID теста", related_name="user_test_test_id_fk",
                                help_text="Уникальный идентификатор теста")
    user_id = models.ForeignKey(User, on_delete=models.SET_DEFAULT,
                                default=1, verbose_name="ID пользователя",
                                related_name="user_test_user_id_fk",
                                help_text="Уникальный идентификатор пользователя")
    success_percent = models.DecimalField(max_digits=10, decimal_places=2,
                                          verbose_name="Процент(%) правильных ответов",
                                          help_text="Процент правильных ответов, которые ввёл ученик ученик")
    status = models.CharField(max_length=256, choices=UserTestStatusChoices.choices,
                              default=UserTestStatusChoices.SUCCESS,
                              verbose_name="Статус",
                              help_text="Статус, отображающий, пройден ли тест учеником")

    class Meta:
        verbose_name = "Сданный тест"
        verbose_name_plural = "Сданные тесты"
