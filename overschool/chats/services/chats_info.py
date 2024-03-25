from channels.db import database_sync_to_async
from chats.models import Chat, Message, UserChat
from common_services.selectel_client import UploadToS3
from courses.models.courses.course import Course, CourseAppeals
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q

User = get_user_model()
s3 = UploadToS3()


def get_avatar(obj):
    if obj.profile.avatar:
        return s3.get_link(obj.profile.avatar.name)
    else:
        # Если нет загруженной фотографии, вернуть ссылку на базовую аватарку
        base_avatar_path = "users/avatars/base_avatar.jpg"
        return s3.get_link(base_avatar_path)


def get_chats_info(user):
    with transaction.atomic():
        user_chats = UserChat.objects.filter(user=user).prefetch_related(
            "chat__message_set", "chat__userchat_set__user__profile"
        )

        total_unread_messages = 0
        chats_data = []

        for user_chat in user_chats:
            chat_data = {
                "id": str(user_chat.chat.id),
                "created_at": str(user_chat.chat.created_at),
                "is_deleted": user_chat.chat.is_deleted,
                "name": user_chat.chat.name,
                "type": user_chat.chat.type,
                "unread": user_chat.unread_messages_count or 0,
            }

            total_unread_messages += user_chat.unread_messages_count or 0

            last_message = user_chat.chat.message_set.order_by("-sent_at").first()
            chat_data["last_message"] = {
                "content": last_message.content if last_message else None,
                "id": last_message.id if last_message else None,
                "sender": last_message.sender.id if last_message else None,
                "sent_at": str(last_message.sent_at) if last_message else None,
            }

            users_data = [
                {
                    "avatar": str(get_avatar(user_chat_user.user)),
                    "email": user_chat_user.user.email,
                    "first_name": user_chat_user.user.first_name,
                    "last_name": user_chat_user.user.last_name,
                    "id": user_chat_user.user.id,
                    "username": user_chat_user.user.username,
                    "user_role": user_chat_user.user_role,
                }
                for user_chat_user in user_chat.chat.userchat_set.select_related(
                    "user__profile"
                )
            ]

            chat_data["senders"] = users_data
            chats_data.append(chat_data)

        response_data = {
            "total_unread": total_unread_messages,
            "chats": chats_data,
        }

    return response_data


@database_sync_to_async
def get_chats_info_async(user):
    with transaction.atomic():
        user_chats = UserChat.objects.filter(user=user).prefetch_related(
            "chat__message_set", "chat__userchat_set__user__profile"
        )

        total_unread_messages = 0
        chats_data = []

        for user_chat in user_chats:
            chat_data = {
                "id": str(user_chat.chat.id),
                "created_at": str(user_chat.chat.created_at),
                "is_deleted": user_chat.chat.is_deleted,
                "name": user_chat.chat.name,
                "type": user_chat.chat.type,
                "unread": user_chat.unread_messages_count or 0,
            }

            total_unread_messages += user_chat.unread_messages_count or 0

            last_message = user_chat.chat.message_set.order_by("-sent_at").first()
            chat_data["last_message"] = {
                "content": last_message.content if last_message else None,
                "id": last_message.id if last_message else None,
                "sender": last_message.sender.id if last_message else None,
                "sent_at": str(last_message.sent_at) if last_message else None,
            }

            users_data = [
                {
                    "avatar": str(get_avatar(user_chat_user.user)),
                    "email": user_chat_user.user.email,
                    "first_name": user_chat_user.user.first_name,
                    "last_name": user_chat_user.user.last_name,
                    "id": user_chat_user.user.id,
                    "username": user_chat_user.user.username,
                    "user_role": user_chat_user.user_role,
                }
                for user_chat_user in user_chat.chat.userchat_set.select_related(
                    "user__profile"
                )
            ]

            chat_data["senders"] = users_data
            chats_data.append(chat_data)

        response_data = {
            "total_unread": total_unread_messages,
            "chats": chats_data,
        }

    return response_data


@database_sync_to_async
def get_unread_appeals_count(user, school):
    admins = (
        User.objects.filter(Q(groups__group__name="Admin") & Q(groups__school=school))
        .distinct()
        .prefetch_related("groups__school", "groups__group")
    )

    if user in admins:
        unread_appeals = CourseAppeals.objects.filter(
            course__school=school, is_read=False
        ).count()
        print("unread_appeals: ", unread_appeals)
        return unread_appeals
    return 0
