from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    Кастомная модель пользователя, расширяющая стандартную AbstractUser
    """
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Телефон",
        help_text="Номер телефона пользователя"
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name="Аватар",
        help_text="Изображение профиля пользователя"
    )
    email_verified = models.BooleanField(
        default=False,
        verbose_name="Email подтвержден",
        help_text="Подтвержден ли адрес электронной почты"
    )
    telegram_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Telegram ID",
        help_text="Идентификатор пользователя в Telegram"
    )

    def clean(self):
        """
        Валидация данных пользователя
        """
        super().clean()
        if self.email:
            self.email = self.email.lower()

    def save(self, *args, **kwargs):
        """
        Переопределение сохранения с предварительной валидацией
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        """
        Строковое представление пользователя
        """
        return f"{self.username} ({self.get_full_name()})"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ['date_joined']
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
            models.Index(fields=['last_name', 'first_name']),
        ]


class Tariff(models.Model):
    """
    Модель тарифного плана
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Название тарифа",
        help_text="Уникальное название тарифного плана"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Стоимость",
        help_text="Цена тарифа в рублях"
    )
    duration = models.PositiveIntegerField(
        default=30,
        verbose_name="Длительность (дней)",
        help_text="Срок действия тарифа в днях"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
        help_text="Доступен ли тариф для выбора"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание",
        help_text="Подробное описание тарифного плана"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    def clean(self):
        """
        Валидация данных тарифа
        """
        if self.price < 0:
            raise ValidationError(_("Цена тарифа не может быть отрицательной"))
        if self.duration <= 0:
            raise ValidationError(_("Длительность должна быть положительным числом"))

    def save(self, *args, **kwargs):
        """
        Переопределение сохранения с предварительной валидацией
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        """
        Строковое представление тарифа
        """
        return f"{self.name} ({self.price} руб., {self.duration} дней)"

    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы"
        ordering = ['price']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['duration']),
        ]


class Feedback(models.Model):
    """
    Модель отзыва/обратной связи
    """
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        help_text="Пользователь, оставивший отзыв",
        related_name="feedbacks",
    )
    text = models.TextField(
        verbose_name="Текст отзыва",
        help_text="Содержимое отзыва",
    )
    rating = models.PositiveSmallIntegerField(
        default=5,
        verbose_name="Рейтинг",
        help_text="Оценка от 1 до 5",
        validators=[
            models.MinValueValidator(1),
            models.MaxValueValidator(5)
        ]
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
        help_text="Когда был оставлен отзыв",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления",
        help_text="Когда отзыв был изменен",
    )

    def clean(self):
        """
        Валидация данных отзыва
        """
        if len(self.text.strip()) < 10:
            raise ValidationError(_("Текст отзыва должен содержать минимум 10 символов"))

    def __str__(self):
        """
        Строковое представление отзыва
        """
        return f"Отзыв от {self.author.username} (Рейтинг: {self.rating})"

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['author']),
            models.Index(fields=['rating']),
            models.Index(fields=['created_at']),
        ]