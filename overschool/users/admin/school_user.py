from django.contrib import admin
from django.contrib.auth.admin import Group, UserAdmin

from users.models import SchoolUser


@admin.register(SchoolUser)
class SchoolUserAdmin(UserAdmin):
    list_display = ("username", "email")
    ordering = ("email",)
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Персональная информация", {"fields": ("email",)}),
        (
            "Права",
            {
                "fields": ("is_active", "is_staff", "groups"),
            },
        ),
        ("Важные даты", {"fields": ("last_login",)}),
    )

    actions = ["link_by_phone", "link_by_post"]

    @admin.action(description="Отправляет уникальную ссылку на телефон")
    def link_by_phone(self, request, queryset):
        ## Отправить ссылку повторно
        queryset.update(status="p")

    @admin.action(description="Отправляет уникальную ссылку на почту")
    def link_by_post(self, request, queryset):
        ## Оправить ссылку повторно
        queryset.update(status="p")

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        userGroup = list(request.user.groups.values_list("name", flat=True))
        if "Администратор" in userGroup:
            if db_field.name == "groups":
                kwargs["queryset"] = Group.objects.exclude(name="Администратор")
        elif "Менеджер" in userGroup:
            if db_field.name == "groups":
                kwargs["queryset"] = Group.objects.filter(name="Студент")
        return super(SchoolUserAdmin, self).formfield_for_manytomany(
            db_field, request, **kwargs
        )

    def get_form(self, request, obj=None, **kwargs):
        defaults = {}
        if obj is None:
            defaults["form"] = self.add_form
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)
