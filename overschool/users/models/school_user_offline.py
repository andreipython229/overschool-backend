from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class CourseOffline(models.Model):
    "Модель курсов оффлайн"
    name = models.CharField(
        max_length=256,
        verbose_name="Название курса",
        help_text="Главное название курса",
    )

    class Meta:
        verbose_name = "Курс Оффлайн"
        verbose_name_plural = "Курсы Оффлайн"

    def __str__(self):
        return f"{self.name}"


class SchoolUserOffline(models.Model):
    "Модель студента оффлайн курса"
    name = models.CharField(
        verbose_name="Имя пользователя",
        max_length=100,
        help_text="ФИО пользователя",
        null=True,
        blank=True,
    )
    email = models.EmailField(
        verbose_name="Почта",
        unique=True,
        help_text="email пользователя",
    )
    contact_number = PhoneNumberField(
        verbose_name="Номер телефона",
        help_text="Номер телефона в формате +375()....... ",
    )
    course = models.ManyToManyField(
        CourseOffline,
        related_name="user_course_offline",
    )

    class Meta:
        verbose_name = "Ученик Оффлайн"
        verbose_name_plural = "Ученики Оффлайн"

    def __str__(self):
        return f"{self.email}  -  {self.contact_number}"
