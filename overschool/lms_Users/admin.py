from .models import User
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email')
    ordering = ("email",)

    def get_fieldsets(self, request, obj=None):
        userGroup = list(request.user.groups.values_list('name', flat=True))
        if "Администратор" in userGroup:
            return (
                (None, {"fields": ("username", "password")}),
                ("Персональная информация", {"fields": ("email",)}),
                (
                    ("Права"),
                    {
                        "fields": (
                            "is_active",
                            "is_staff",
                            "groups",
                        ),
                    },
                ),
                ("Важные даты", {"fields": ("last_login",)}),
            )
        elif "Менеджер" in userGroup:
            pass
        elif "Редактор" in userGroup:
            pass
        elif "Преподаватель" in userGroup:
            pass

        return super(UserAdmin, self).get_fieldsets(request, obj)

