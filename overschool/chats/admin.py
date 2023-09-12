from django.contrib import admin

from .models import Chat, Message, UserChat


@admin.register(Chat, Message, UserChat)
class UserHomeworkAdmin(admin.ModelAdmin):
    pass
