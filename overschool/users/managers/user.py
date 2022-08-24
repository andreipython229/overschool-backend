from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import User
from phonenumber_field.phonenumber import PhoneNumber


class UserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """

    def create_user(self, username, email, phone_number, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """

        if not username:
            raise ValueError("Имя пользователя должно быть указано")

        if not (email and phone_number):
            raise ValueError("Почта или телефон должны быть указаны")

        if email:
            email = self.normalize_email(email)

        if phone_number:
            phone_number = PhoneNumber.from_string(phone_number).as_e164

        user = self.model(username=username, email=email, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, email, phone_number, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(username, email, phone_number, password, **extra_fields)
