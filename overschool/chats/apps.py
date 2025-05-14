from django.apps import AppConfig


class ChatsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "chats"

    def ready(self):
        from chats.signals import (
            new_message,
            send_unread_appeals_count,
            update_user_unread_message,
        )
        from courses.models.courses.course import CourseAppeals
        from django.db.models.signals import post_save

        from .models import Message, UserChat

        post_save.connect(new_message, sender=Message)
        post_save.connect(update_user_unread_message, sender=UserChat)
        post_save.connect(send_unread_appeals_count, sender=CourseAppeals)
