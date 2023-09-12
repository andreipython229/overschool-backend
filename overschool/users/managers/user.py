import unicodedata

from django.contrib.auth.models import UserManager as _UserManager
from django.db.transaction import atomic
from phonenumber_field.phonenumber import PhoneNumber


class UserManager(_UserManager):
    def _create_user(
        self, username, email, phone_number, password=None, **extra_fields
    ):
        if not username:
            raise ValueError("Имя пользователя должно быть указано")

        if not (email or phone_number):
            raise ValueError("Почта или телефон должны быть указаны")

        if not password:
            raise ValueError("Пароль должен быть указан")

        if email:
            email = self.normalize_email(email)

        if phone_number:
            phone_number = PhoneNumber.from_string(phone_number).as_e164

        user = self.model(
            username=unicodedata.normalize("NFKC", username),
            email=email,
            phone_number=phone_number,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        print(user)
        return user

    @atomic
    def create_user(
        self, username, email=None, phone_number=None, password=None, **extra_fields
    ):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        return self._create_user(
            username, email, phone_number, password, **extra_fields
        )

    @atomic
    def create_superuser(
        self, username, email=None, phone_number=None, password=None, **extra_fields
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self._create_user(
            username, email, phone_number, password, **extra_fields
        )
