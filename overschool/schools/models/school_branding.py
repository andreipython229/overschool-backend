from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from schools.models import School


class SchoolBranding(models.Model):
    school = models.OneToOneField(
        School, on_delete=models.CASCADE, related_name="branding", unique=True
    )
    platform_logo = models.ImageField(
        upload_to="branding/logos/",
        verbose_name="Логотип платформы",
        null=True,
        blank=True,
    )
    email = models.EmailField(verbose_name="Email", null=True, blank=True)
    phone = PhoneNumberField(
        verbose_name="Номер телефона", help_text="Номер телефона", null=True, blank=True
    )
    unp = models.CharField(max_length=20, verbose_name="УНП", null=True, blank=True)
    full_organization_name = models.CharField(
        max_length=500,
        verbose_name="Полное название организации",
        null=True,
        blank=True,
    )
    address = models.CharField(
        max_length=500, verbose_name="Адрес", null=True, blank=True
    )

    def __str__(self):
        return f"Ребрендинг для школы: {self.school.name}"

    class Meta:
        verbose_name = "Ребрендинг школы"
        verbose_name_plural = "Ребрендинги школ"
