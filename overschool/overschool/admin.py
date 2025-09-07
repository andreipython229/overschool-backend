from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()

# Отключаем автоматическую регистрацию User модели
admin.site.unregister(User)


# Регистрируем кастомный UserAdmin БЕЗ last_login
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Кастомный админ для пользователей БЕЗ last_login"""

    # Используем ТОЛЬКО стандартные поля Django
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'email')}),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
        ('Важные даты', {'fields': ('date_joined',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    # Явно исключаем last_login
    exclude = ('last_login',)

    # ИСПРАВЛЕНИЕ: Убираем filter_horizontal полностью
    filter_horizontal = ()

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)