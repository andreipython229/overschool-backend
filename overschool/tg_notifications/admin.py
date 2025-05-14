from django.contrib import admin

from .models import TgUsers, Notifications, CompletedCoursesNotificationsLog


@admin.register(TgUsers)
class TgUsersAdmin(admin.ModelAdmin):
    pass


@admin.register(Notifications)
class NotificationsAdmin(admin.ModelAdmin):
    pass


@admin.register(CompletedCoursesNotificationsLog)
class CompletedCoursesNotificationsLogAdmin(admin.ModelAdmin):
    pass