from django.contrib.auth.base_user import BaseUserManager


class SchoolUserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Вы не ввели Email")
        user = self.model(
            email=self.normalize_email(email),
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

# class UserManager(auth_models.BaseUserManager):
#     """На рассмотрение, моя модель(можно поменять)"""
#     def create_user(
#             self,
#             first_name: str,
#             last_name: str,
#             email: str,
#             password: str = None,
#             is_staff=False,
#             is_superuser=False,
#     ) -> "User":
#         if not email:
#             raise ValueError("User must have an email")
#         if not first_name:
#             raise ValueError("User must have a first name")
#         if not last_name:
#             raise ValueError("User must have a last name")
#
#         user = self.model(email=self.normalize_email(email))
#         user.first_name = first_name
#         user.last_name = last_name
#         user.set_password(password)
#         user.is_active = True
#         user.is_staff = is_staff
#         user.is_superuser = is_superuser
#         user.save()
#
#         return user

    def create_user(self, email, password):
        return self._create_user(email, password, is_staff=False)

    def create_superuser(self, email, password):
        return self._create_user(email, password, is_staff=True, is_superuser=True)
