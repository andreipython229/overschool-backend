from common_services.mixins import OrderMixin, TimeStampMixin
from common_services.services import limit_size
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from oauthlib.common import urldecode
from schools.managers import SchoolManager

User = get_user_model()


class TariffPlan(models.TextChoices):
    "Тарифы для школы"
    INTERN = "Intern", "Intern"
    JUNIOR = "Junior", "Junior"
    MIDDLE = "Middle", "Middle"
    SENIOR = "Senior", "Senior"


class Tariff(models.Model):
    id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID тарифа",
        help_text="Уникальный идентификатор тарифа",
    )
    name = models.CharField(
        max_length=10, choices=TariffPlan.choices, default=TariffPlan.INTERN
    )
    number_of_courses = models.IntegerField(
        null=True, blank=True, verbose_name="Количество курсов"
    )
    students_per_month = models.IntegerField(
        null=True, blank=True, verbose_name="Количество учеников в месяц"
    )
    total_students = models.IntegerField(
        null=True, blank=True, verbose_name="Общее количество учеников"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")

    def __str__(self):
        return f"{self.name} - {self.price}"


class School(TimeStampMixin, OrderMixin):
    """Модель школы"""

    school_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID школы",
        help_text="Уникальный идентификатор школы",
    )
    name = models.CharField(
        max_length=256,
        verbose_name="Название",
        help_text="Название школы",
        unique=True,
    )
    tariff = models.ForeignKey(
        Tariff,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Тариф",
        help_text="Тариф школы",
    )
    used_trial = models.BooleanField(
        default=False,
        verbose_name="Пробный тариф использован",
        help_text="Флаг, указывающий, использовал ли пользователь пробный тариф",
    )
    purchased_tariff_end_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Окончание оплаченного тарифа",
        help_text="Дата окончания оплаченного тарифа",
    )
    trial_end_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Дата окончания пробного периода",
        help_text="Дата, когда пробный период истекает",
    )
    avatar = models.ImageField(
        verbose_name="Фотография",
        help_text="Фотография школы",
        validators=[limit_size],
        blank=True,
        null=True,
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="owner_school",
        verbose_name="Владелец школы",
        help_text="ID владельца школы",
    )

    objects = SchoolManager()

    def check_trial_status(self):
        # Проверка статуса пробного периода
        if (
            self.used_trial
            and self.trial_end_date
            and self.trial_end_date <= timezone.now()
        ):
            self.tariff = Tariff.objects.get(name=TariffPlan.INTERN.value)
            self.trial_end_date = None
            self.used_trial = True
        # Проверка оплаты тарифа
        if (
            self.purchased_tariff_end_date
            and self.purchased_tariff_end_date <= timezone.now()
        ):
            self.tariff = Tariff.objects.get(name=TariffPlan.INTERN.value)
            self.purchased_tariff_end_date = None

        self.save()

    def avatar_url(self):
        if self.avatar:
            url = urldecode(self.avatar.url)
            return url[0][0]
        return None

    def __str__(self):
        return str(self.school_id) + " " + str(self.name)

    class Meta:
        verbose_name = "Школа"
        verbose_name_plural = "Школы"
        constraints = [
            models.UniqueConstraint(fields=["order"], name="unique_school_order"),
        ]
