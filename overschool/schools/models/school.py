from common_services.mixins import OrderMixin, TimeStampMixin
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
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
    number_of_staff = models.IntegerField(
        null=True, blank=True, verbose_name="Количество сотрудников"
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

    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы"


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
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="owner_school",
        verbose_name="Владелец школы",
        help_text="ID владельца школы",
    )
    offer_url = models.URLField(
        max_length=200,
        default="",
        blank=True,
        null=True,
        verbose_name="url договора оферты",
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

    def __str__(self):
        return str(self.school_id) + " " + str(self.name)

    class Meta:
        verbose_name = "Школа"
        verbose_name_plural = "Школы"
        constraints = [
            models.UniqueConstraint(fields=["order"], name="unique_school_order"),
        ]


class SchoolStatistics(models.Model):
    school = models.OneToOneField(
        School,
        on_delete=models.CASCADE,
        verbose_name="Школа",
        related_name="statistics",
    )

    def get_lessons_count(self):
        BaseLesson = apps.get_model("courses", "BaseLesson")
        return BaseLesson.objects.filter(
            section__course__school__name=self.school.name
        ).count()

    def get_last_update_date(self):
        BaseLesson = apps.get_model("courses", "BaseLesson")
        last_lesson = (
            BaseLesson.objects.filter(section__course__school__name=self.school.name)
            .order_by("-updated_at")
            .values("updated_at")
            .first()
        )
        return last_lesson["updated_at"] if last_lesson else None

    def get_completed_lessons_count(self, start_date=None, end_date=None):
        UserProgressLogs = apps.get_model("courses", "UserProgressLogs")
        user_progress_logs = UserProgressLogs.objects.filter(
            completed=True,
            lesson__section__course__school__name=self.school.name,
        )
        if start_date and end_date:
            user_progress_logs = user_progress_logs.filter(
                updated_at__gte=start_date, updated_at__lte=end_date
            )
        if start_date:
            user_progress_logs = user_progress_logs.filter(updated_at__gte=start_date)
        if end_date:
            user_progress_logs = user_progress_logs.filter(updated_at__lte=end_date)

        return user_progress_logs.distinct().count()

    def get_added_students_count(self, start_date=None, end_date=None):
        UserGroup = apps.get_model("users", "UserGroup")
        students_count = UserGroup.objects.filter(
            school__name=self.school.name, group__name="Student"
        )
        if start_date and end_date:
            students_count = students_count.filter(
                created_at__gte=start_date, created_at__lte=end_date
            )
        if start_date:
            students_count = students_count.filter(created_at__gte=start_date)
        if end_date:
            students_count = students_count.filter(created_at__lte=end_date)

        return students_count.distinct().count()

    def __str__(self):
        return f"Статистика для школы {self.school.name}"

    class Meta:
        verbose_name = "Статистика школы"
        verbose_name_plural = "Статистика школ"


@receiver(post_save, sender=School)
def create_school_statistics(sender, instance, created, **kwargs):
    if created:
        SchoolStatistics.objects.create(
            school=instance,
        )
