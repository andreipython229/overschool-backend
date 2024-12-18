from common_services.mixins import TimeStampMixin
from common_services.services import TruncateFileName, limit_image_size
from django.conf import settings
from django.db import models
from django.utils.timezone import now, timedelta
from schools.models import School


class Box(models.Model):
    icon = models.ImageField(
        help_text="Иконка коробки",
        verbose_name="Иконка коробки",
        max_length=300,
        validators=[limit_image_size],
        upload_to=TruncateFileName(300),
        blank=True,
        null=True,
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="boxes_school",
        verbose_name="ID школы",
        help_text="ID школы",
    )
    name = models.CharField(
        max_length=300,
        help_text="Название коробки",
        verbose_name="Название коробки",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена",
        help_text="Цена коробки",
    )
    quantity = models.PositiveIntegerField(
        help_text="Количество коробок в наборе",
        verbose_name="Количество коробок в наборе",
    )
    bonus_quantity = models.PositiveIntegerField(
        help_text="Количество бонусных коробок",
        default=0,
        verbose_name="Бонусные коробки",
    )
    is_active = models.BooleanField(
        help_text="Активировать коробку",
        default=True,
        verbose_name="Статус активности",
    )
    auto_deactivation_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Время авто деактивации",
        help_text="Время авто деактивации коробки",
    )

    def deactivate_if_needed(self):
        if self.auto_deactivation_time and now() > self.auto_deactivation_time:
            self.is_active = False
            self.save()

    def __str__(self):
        return self.name


class Prize(models.Model):
    icon = models.ImageField(
        help_text="Иконка приза",
        verbose_name="Иконка приза",
        max_length=300,
        validators=[limit_image_size],
        upload_to=TruncateFileName(300),
        blank=True,
        null=True,
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="prizes_school",
        verbose_name="ID школы",
        help_text="ID школы",
    )
    name = models.CharField(
        max_length=300,
        help_text="Название приза",
        verbose_name="Название приза",
    )
    drop_chance = models.FloatField(
        help_text="Шанс выпадения приза",
        verbose_name="Шанс выпадения (%)",
    )
    guaranteed_box_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Количество коробок для гарантированного приза",
        verbose_name="Количество коробок для гарантированного приза",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Активировать приз",
        verbose_name="Статус активности",
    )

    def __str__(self):
        return self.name


class BoxPrize(models.Model):
    box = models.ForeignKey(
        Box,
        on_delete=models.CASCADE,
        related_name="prizes",
        help_text="Коробка",
        verbose_name="Коробка",
    )
    prize = models.ForeignKey(
        Prize,
        on_delete=models.CASCADE,
        related_name="boxes",
        help_text="Приз",
        verbose_name="Приз",
    )

    def __str__(self):
        return f"{self.prize.name} в {self.box.name}"


class UserPrize(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="prizes",
        help_text="Пользователь",
        verbose_name="Пользователь",
    )
    prize = models.ForeignKey(
        Prize,
        on_delete=models.CASCADE,
        related_name="user_prizes",
        help_text="Приз",
        verbose_name="Приз",
    )
    received_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Дата и время получения приза",
        verbose_name="Дата получения",
    )

    def __str__(self):
        return f"{self.user.email} - {self.prize.name}"


class Payment(TimeStampMixin, models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments",
        help_text="Пользователь",
        verbose_name="Пользователь",
    )
    box = models.ForeignKey(
        Box,
        on_delete=models.SET_NULL,
        related_name="payments",
        null=True,
        help_text="Коробка",
        verbose_name="Коробка",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Сумма платежа",
        verbose_name="Сумма",
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="ID школы",
        help_text="ID школы",
    )
    invoice_no = models.IntegerField(
        verbose_name="Номер счета", help_text="Номер счета", default=0, null=True
    )
    payment_status = models.CharField(
        max_length=50,
        choices=[
            ("pending", "В ожидании"),
            ("completed", "Завершен"),
            ("failed", "Неуспешен"),
        ],
        default="pending",
        verbose_name="Статус оплаты",
    )

    def __str__(self):
        return f"Платеж {self.id} - {self.user.username} - {self.box.name} - {self.box.invoice_no}"
