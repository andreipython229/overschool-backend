from django.contrib import admin

from .models import OverAiChat, BotResponse, UserMessage, AIProvider


@admin.register(OverAiChat)
class OverAiChatAdmin(admin.ModelAdmin):
    pass


@admin.register(BotResponse)
class BotResponseAdmin(admin.ModelAdmin):
    pass


@admin.register(UserMessage)
class UserMessageAdmin(admin.ModelAdmin):
    pass


@admin.register(AIProvider)
class AIProviderAdmin(admin.ModelAdmin):
    pass
