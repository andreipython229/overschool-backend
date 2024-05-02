from django.contrib import admin

from .models import TgUsers, Notifications


@admin.register(TgUsers)
class TgUsersAdmin(admin.ModelAdmin):
    pass


@admin.register(Notifications)
class NotificationsAdmin(admin.ModelAdmin):
    pass