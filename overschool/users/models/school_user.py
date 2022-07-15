from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.contrib.auth import models as auth_models
from django.core.mail import send_mail
from django.db import models
from django.dispatch import receiver
from django.urls import reverse
from django_rest_passwordreset.signals import reset_password_token_created
from users.managers import SchoolUserManager


class SchoolUser(AbstractUser, PermissionsMixin):
    email = models.EmailField("Почта", unique=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = SchoolUserManager()

    class Meta:
        app_label = "users"

    def __str__(self):
        return self.username


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    email_plaintext_message = "{}?token={}".format(reverse('password_reset:reset-password-request'),
                                                   reset_password_token.key)

    send_mail(
        # title:
        "Password Reset for {title}".format(title="Some website title"),
        # message:
        email_plaintext_message,
        # from:
        "noreply@somehost.local",
        # to:
        [reset_password_token.user.email]
    )