from django.apps import AppConfig


class ChatsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chats'

    def ready(self):
        from .models import Message, UserChat

        from django.db.models.signals import post_save
        from chats.signals import new_message, update_user_unread_message

        post_save.connect(new_message, sender=Message)
        post_save.connect(update_user_unread_message, sender=UserChat)
