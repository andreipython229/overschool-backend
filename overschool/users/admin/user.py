from django.contrib import admin
from users.forms import UserChangeForm, UserCreationForm
from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ("username", "email", "phone_number")
    ordering = ("username",)
    list_filter = ("is_superuser", "is_staff", "is_active")
    search_fields = ("username", "email", "phone_number")
    fieldsets = (
        (None, {"fields": ("username", "email", "phone_number" "password")}),
        ("Personal info", {"classes": ("collapse",), "fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {
                "classes": ("collapse",),
                "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            },
        ),
        ("Important dates", {"classes": ("collapse",), "fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "fields": ("username", "email", "phone_number", "password1", "password2"),
            },
        ),
    )
