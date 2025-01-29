from django.contrib import admin

from .models import Chat, Message, UserChat


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "type", "is_deleted", "created_at"]
    list_filter = ["name", "type", "is_deleted"]
    search_fields = ["name"]


@admin.register(Message, UserChat)
class UserChatAdmin(admin.ModelAdmin):
    pass
