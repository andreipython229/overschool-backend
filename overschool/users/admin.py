from django.contrib import admin
from users.models import Tariff, Feedback

# ПОЛНОСТЬЮ УБИРАЕМ ВСЕ РЕГИСТРАЦИИ ПОЛЬЗОВАТЕЛЕЙ
# Пусть Django использует стандартный UserAdmin

@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    fieldsets = (
        (None, {
            'fields': ('name', 'price', 'is_active')
        }),
        ('Дополнительно', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('author', 'created_at')
    search_fields = ('author__username', 'text')
    readonly_fields = ('created_at',)