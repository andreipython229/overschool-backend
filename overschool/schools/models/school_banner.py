from courses.models.students.students_group import StudentsGroup
from django.db import models
from schools.models import School
from users.models.user import User


class Banner(models.Model):
    title = models.CharField(
        max_length=255, verbose_name="Заголовок", help_text="Заголовок баннера"
    )
    description = models.TextField(
        verbose_name="Описание", help_text="Описание баннера"
    )
    is_active = models.BooleanField(
        default=False, verbose_name="Активный", help_text="Активный баннер"
    )
    link = models.URLField(
        max_length=255, verbose_name="Ссылка", help_text="Ссылка на баннер"
    )
    groups = models.ManyToManyField(
        StudentsGroup, related_name="banners", verbose_name="Группы", blank=True
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="banners",
        verbose_name="Баннер школы",
        help_text="Баннер школы",
    )

    class Meta:
        verbose_name = "Баннер"
        verbose_name_plural = "Баннеры"

    def __str__(self):
        return f"{self.title} - {self.school}"


class BannerClick(models.Model):
    banner = models.ForeignKey(
        Banner,
        on_delete=models.CASCADE,
        related_name="clicks",
        verbose_name="Баннер",
        help_text="Баннер",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="banner_clicks",
        verbose_name="Пользователь",
        help_text="Пользователь",
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата и время перехода",
        help_text="Дата и время перехода",
    )

    class Meta:
        verbose_name = "Переход по баннеру"
        verbose_name_plural = "Переходы по баннерам"

    def __str__(self):
        return f"Переход по баннеру {self.banner} с IP {self.ip_address}"


class BannerAccept(models.Model):
    banner = models.ForeignKey(
        Banner,
        on_delete=models.CASCADE,
        related_name="accepts",
        verbose_name="Баннер",
        help_text="Баннер",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="banner_accepts",
        verbose_name="Пользователь",
        help_text="Пользователь",
    )
    is_accepted = models.BooleanField(
        default=False,
        verbose_name="Пользователь принял баннер",
        help_text="Пользователь принял баннер",
    )

    class Meta:
        verbose_name = "Принятый баннер"
        verbose_name_plural = "Принятыe баннеры"

    def __str__(self):
        return f"Принятый баннер {self.banner} пользователем {self.user}"
