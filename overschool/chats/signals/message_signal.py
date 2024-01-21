import json
from django.db.models.signals import post_save
from django.dispatch import receiver
from chats.models import Message, UserChat
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async
from chats.services import get_chats_info


channel_layer = get_channel_layer()


@receiver(post_save,  sender=Message)
def new_message(sender, instance, created, **kwargs):
    if created:
        chat = instance.chat

        user_chats = chat.userchat_set.all()
        users = [user_chat.user for user_chat in user_chats]

        if users:
            for user in users:
                message = get_chats_info(user)
                async_to_sync(channel_layer.group_send)(f"user_{user.id}_group", {
                    'type': 'user_inform',
                    'user_id': user.id,
                    'message': message
                })


@receiver(post_save, sender=UserChat)
def update_user_unread_message(sender, instance, **kwargs):
    if instance.unread_messages_count == 0:
        user = instance.user
        message = get_chats_info(user)
        async_to_sync(channel_layer.group_send)(f"user_{user.id}_group", {
            'type': 'user_inform',
            'user_id': user.id,
            'message': message
        })
