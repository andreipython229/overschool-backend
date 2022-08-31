from django.contrib import auth
from django.contrib.auth.base_user import BaseUserManager
from phonenumber_field.phonenumber import PhoneNumber


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, email, phone_number, password, **extra_fields):
        if not username:
            raise ValueError("Имя пользователя должно быть указано")

        if not (email or phone_number):
            raise ValueError("Почта или телефон должны быть указаны")

        if email:
            email = self.normalize_email(email)

        if phone_number:
            phone_number = PhoneNumber.from_string(phone_number).as_e164

        user = self.model(username=username, email=email, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email, phone_number, password, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        return self._create_user(username, email, phone_number, password, **extra_fields)

    def create_superuser(self, username, email, phone_number, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self._create_user(username, email, phone_number, password, **extra_fields)

    def with_perm(self, perm, is_active=True, include_superusers=True, backend=None, obj=None):
        if backend is None:
            backends = auth._get_backends(return_tuples=True)
            if len(backends) == 1:
                backend, _ = backends[0]
            else:
                raise ValueError(
                    "You have multiple authentication backends configured and "
                    "therefore must provide the `backend` argument."
                )
        elif not isinstance(backend, str):
            raise TypeError("backend must be a dotted import path string (got %r)." % backend)
        else:
            backend = auth.load_backend(backend)
        if hasattr(backend, "with_perm"):
            return backend.with_perm(
                perm,
                is_active=is_active,
                include_superusers=include_superusers,
                obj=obj,
            )
        return self.none()
