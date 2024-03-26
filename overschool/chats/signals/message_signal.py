from asgiref.sync import async_to_sync, sync_to_async
from channels.layers import get_channel_layer
from chats.models import Message, UserChat
from chats.services import get_chats_info
from courses.models.courses.course import CourseAppeals
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver

channel_layer = get_channel_layer()
User = get_user_model()


@receiver(post_save, sender=Message)
def new_message(sender, instance, created, **kwargs):
    if created:
        chat = instance.chat

        user_chats = chat.userchat_set.all()
        users = [user_chat.user for user_chat in user_chats]

        if users:
            for user in users:
                message = get_chats_info(user)
                async_to_sync(channel_layer.group_send)(
                    f"user_{user.id}_group",
                    {"type": "user_inform", "user_id": user.id, "message": message},
                )


@receiver(post_save, sender=UserChat)
def update_user_unread_message(sender, instance, **kwargs):
    if instance.unread_messages_count == 0:
        user = instance.user
        message = get_chats_info(user)
        async_to_sync(channel_layer.group_send)(
            f"user_{user.id}_group",
            {"type": "user_inform", "user_id": user.id, "message": message},
        )


@receiver(post_save, sender=CourseAppeals)
def send_unread_appeals_count(sender, instance, created, **kwargs):
    if created:
        school = instance.course.school
        unread_appeals = CourseAppeals.objects.filter(
            course__school=school, is_read=False
        ).count()

        admins = (
            User.objects.filter(
                Q(groups__group__name="Admin") & Q(groups__school=school)
            )
            .distinct()
            .prefetch_related("groups__school", "groups__group")
        )

        for admin in admins:
            async_to_sync(channel_layer.group_send)(
                f"user_{admin.id}_group",
                {
                    "type": "unread_appeals_count",
                    "unread_count": unread_appeals,
                    "school_id": school.school_id,
                },
            )
