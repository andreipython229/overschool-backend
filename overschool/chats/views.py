from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .constants import CustomResponses
from .models import Chat, ChatLink, Message, UserChat
from .request_params import ChatParams, UserParams
from .schemas import ChatSchemas
from .serializers import ChatSerializer, MessageSerializer

User = get_user_model()


def is_user_exist(user_id):
    try:
        user = User.objects.get(id=user_id)
        return user
    except User.DoesNotExist:
        return False


def is_chat_participant(user, chat):
    user_chats = UserChat.objects.filter(chat=chat)
    for user_chat in user_chats:
        if user == user_chat.user:
            return True

    return False


def is_object_exist(pk, object):
    try:
        post = object.objects.get(pk=pk)
        return post
    except object.DoesNotExist:
        return False


class AllChatSerializer(serializers.Serializer):
    pass


class ChatListCreate(LoggingMixin, WithHeadersViewSet, APIView):
    """
    - Список всех чатов
    - Создание чата
    """

    serializer_class = AllChatSerializer
    parser_classes = (MultiPartParser,)
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(
            group__name__in=[
                "Admin",
                "Teacher",
                "Student",
            ]
        ).exists() or user.email == "student@coursehub.ru":
            return permissions
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    @swagger_auto_schema(
        responses=ChatSchemas.chats_for_user_schema,
        operation_description="Get all chats for user",
        operation_summary="Get all chats for user",
        tags=["chats"],
    )
    def get(self, request, *args, **kwargs):
        user = self.request.user
        chats_for_user = UserChat.objects.filter(user=user)
        chats_list = [str(chat.chat) for chat in chats_for_user]

        chats = Chat.objects.filter(id__in=chats_list)

        serializer = ChatSerializer(chats, many=True, context={"request": self.request})

        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses=ChatSchemas.chat_uuid_schema,
        manual_parameters=[UserParams.user_id],
        operation_description="Get or create PERSONAL chat with user",
        operation_summary="Get or create PERSONAL chat with user",
        tags=["chats"],
    )
    def post(self, request, *args, **kwargs):
        chat_creator = self.request.user
        role_creator = request.data.get("role_name")
        role_reciever = request.data.get("role_reciever")
        print(role_creator + " and " + role_reciever)
        role1 = ""
        role2 = ""
        if role_creator == "Admin":
            role1 = "Администратор"
            role2 = "Студент"
        elif role_creator == "Teacher":
            role1 = "Ментор"
            role2 = "Студент"
        elif role_creator == "Student":
            role1 = "Ментор"
            role2 = "Студент"
            role_reciever = "Teacher"

        chat_reciever_id = request.data.get("user_id")

        chat_reciever = is_user_exist(chat_reciever_id)
        if chat_reciever is False:
            return Response(
                {"error": "User does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )

        existed_chat_id = UserChat.get_existed_chat_id_by_type(
            chat_creator, chat_reciever, type="PERSONAL"
        )
        if existed_chat_id:
            existed_chat = Chat.objects.get(id=existed_chat_id)
            user_chat_serializer = ChatSerializer(
                existed_chat, context={"request": self.request}
            )
            return Response(user_chat_serializer.data, status=status.HTTP_200_OK)
        else:
            chat = Chat.objects.create(
                type="PERSONAL",
                name=f"{role1}:"
                f'{chat_creator.email if role_creator != "Student" else chat_reciever.email}:'
                f"{role2}:"
                f'{chat_reciever.email if role_creator != "Student" else chat_creator.email}',
            )
            user_chats = [
                UserChat(user=chat_creator, chat=chat, user_role=role_creator),
                UserChat(user=chat_reciever, chat=chat, user_role=role_reciever),
            ]

            UserChat.objects.bulk_create(user_chats)

            Message.objects.create(
                chat=chat,
                sender=chat_creator if role_creator != "Student" else chat_reciever,
                content="""
                    Приветствую Вас в чате техподдержки!😊
                    Если Вам будет нужна помощь, пожалуйста, напишите мне)👋""",
            )

            existed_chat_id = UserChat.get_existed_chat_id_by_type(
                chat_creator, chat_reciever, "PERSONAL"
            )
            if existed_chat_id:
                existed_chat = Chat.objects.get(id=existed_chat_id)
                user_chat_serializer = ChatSerializer(
                    existed_chat, context={"request": self.request}
                )
                return Response(
                    user_chat_serializer.data, status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {"error": "Chat does not created"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

    @action(detail=False, methods=["POST"])
    @swagger_auto_schema(
        responses=ChatSchemas.chat_uuid_schema,
        manual_parameters=[
            openapi.Parameter(
                "teacher_id",
                openapi.IN_QUERY,
                description="ID учителя",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "student_id",
                openapi.IN_QUERY,
                description="ID ученика",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "chat_id",
                openapi.IN_QUERY,
                description="ID чата",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "message",
                openapi.IN_QUERY,
                description="Сообщение для чата",
                type=openapi.TYPE_STRING,
                required=False,  # Установить на True, если параметр обязателен
            ),
        ],
        operation_description="Get or create chat with user",
        operation_summary="Get or create chat with user",
        tags=["chats"],
    )
    def create_personal_chat(self, request):
        teacher_id = self.request.query_params.get("teacher_id")
        student_id = self.request.query_params.get("student_id")
        message = request.data.get("message", "")
        chat_id = request.query_params.get("chat_id")

        teacher = User.objects.filter(id=teacher_id).first()
        student = User.objects.filter(id=student_id).first()

        if not teacher or not student:
            return Response(
                {"detail": "Неверные идентификаторы учителя и/или ученика."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Валидация и проверка существования группового чата
        group_chat = Chat.objects.filter(id=chat_id, type="GROUP").first()
        if not group_chat:
            return Response(
                {
                    "detail": "Групповой чат с указанным ID не существует или не является групповым."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Получаем имена учителя и студента
        teacher_name = teacher.username
        student_name = student.username

        # Создаем название чата с именами учителя и студента
        chat_name = _("{} : {}").format(student_name, teacher_name)

        # Создаем персональный чат с указанным названием и типом "PERSONAL"
        personal_chat = Chat.objects.create(name=chat_name, type="PERSONAL")

        # Добавляем учителя и ученика в персональный чат
        UserChat.objects.create(user=teacher, chat=personal_chat)
        UserChat.objects.create(user=student, chat=personal_chat)

        # Если передано сообщение, создаем первое сообщение в персональном чате
        if message:
            Message.objects.create(chat=personal_chat, sender=teacher, content=message)

        # Создаем связь между персональным чатом и групповым чатом
        ChatLink.objects.create(parent=group_chat, child=personal_chat)

        return Response(
            {"detail": "Персональный чат успешно создан."},
            status=status.HTTP_201_CREATED,
        )


class ChatDetailDelete(LoggingMixin, WithHeadersViewSet, APIView):
    """
    - Детали чата
    - Удаление / восстановление чата
    """

    serializer_class = AllChatSerializer
    parser_classes = (MultiPartParser,)
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        responses=ChatSchemas.chat_schema,
        manual_parameters=[ChatParams.uuid],
        operation_description="Get chat by uuid",
        operation_summary="Get chat by uuid",
        tags=["chats"],
    )
    def get(self, request, *args, **kwargs):
        pk = self.kwargs["chat_uuid"]
        chat = is_object_exist(pk, Chat)
        if chat is False:
            return Response(
                CustomResponses.chat_not_exist, status=status.HTTP_400_BAD_REQUEST
            )

        user = self.request.user
        user_is_chat_participant = is_chat_participant(user, chat)
        if user_is_chat_participant is False:
            return Response(
                CustomResponses.no_permission, status=status.HTTP_403_FORBIDDEN
            )

        serializer = ChatSerializer(chat, context={"request": self.request})

        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses=ChatSchemas.chat_schema,
        manual_parameters=[
            openapi.Parameter(
                "chat_uuid",
                openapi.IN_PATH,
                description="UUID группового чата для удаления",
                type=openapi.TYPE_STRING,
                required=True,
            ),
        ],
        operation_description="Delete chat by uuid",
        operation_summary="Delete chat by uuid",
        tags=["chats"],
    )
    def delete(self, request, *args, **kwargs):
        pk = self.kwargs["chat_uuid"]
        chat = is_object_exist(pk, Chat)
        if chat is False:
            return Response(
                CustomResponses.chat_not_exist, status=status.HTTP_400_BAD_REQUEST
            )

        user = self.request.user
        user_is_chat_participant = is_chat_participant(user, chat)
        if user_is_chat_participant is False:
            return Response(
                CustomResponses.no_permission, status=status.HTTP_403_FORBIDDEN
            )

        # Удалите все связанные персональные чаты и затем удалите групповой чат
        chat.personal_chats.all().delete()
        chat.delete()

        return Response(
            {"detail": "Групповой чат и связанные персональные чаты успешно удалены."},
            status=status.HTTP_204_NO_CONTENT,
        )

    @swagger_auto_schema(
        responses=ChatSchemas.chat_schema,
        manual_parameters=[ChatParams.uuid, ChatParams.name, ChatParams.is_deleted],
        operation_description="Delete or restore chat by uuid, change chat name",
        operation_summary="Delete or restore chat by uuid, change chat name",
        tags=["chats"],
    )
    def patch(self, request, *args, **kwargs):
        pk = self.kwargs["chat_uuid"]
        chat = is_object_exist(pk, Chat)
        if chat is False:
            return Response(
                CustomResponses.chat_not_exist, status=status.HTTP_400_BAD_REQUEST
            )

        user = self.request.user
        user_is_chat_participant = is_chat_participant(user, chat)
        if user_is_chat_participant is False:
            return Response(
                CustomResponses.no_permission, status=status.HTTP_403_FORBIDDEN
            )
        if request.data.get("name"):
            chat.name = request.data.get("name")
        if request.data.get("is_deleted") == "true":
            chat.is_deleted = True
        if request.data.get("is_deleted") == "false":
            chat.is_deleted = False
        chat.save()
        serializer = ChatSerializer(chat, context={"request": self.request})

        return Response(serializer.data, status=status.HTTP_200_OK)


class MessageList(LoggingMixin, WithHeadersViewSet, APIView):
    """
    - Сообщения чата
    """

    serializer_class = AllChatSerializer
    parser_classes = (MultiPartParser,)
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        responses=ChatSchemas.messages_schema,
        manual_parameters=[ChatParams.uuid],
        operation_description="Get messages for chat by uuid",
        operation_summary="Get messages for chat by uuid",
        tags=["chats"],
    )
    def get(self, request, *args, **kwargs):
        pk = self.kwargs["chat_uuid"]
        chat = is_object_exist(pk, Chat)
        if chat is False:
            return Response(
                CustomResponses.chat_not_exist, status=status.HTTP_400_BAD_REQUEST
            )

        user = self.request.user
        user_is_chat_participant = is_chat_participant(user, chat)
        if user_is_chat_participant is False:
            return Response(
                CustomResponses.no_permission, status=status.HTTP_403_FORBIDDEN
            )

        messages = Message.objects.filter(chat=chat)
        serializer = MessageSerializer(
            messages, many=True, context={"request": self.request}
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


from courses.models import StudentsGroup
from rest_framework.decorators import api_view


@api_view(["POST"])
def create_or_update_group_chat(request, group_id):

    if not group_id:
        return Response("Должны быть group_id")

    try:
        group = StudentsGroup.objects.get(pk=group_id)
    except StudentsGroup.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    admins = User.objects.filter(
        groups__school=group.course_id.school, groups__group__name__in=["Admin"]
    )

    # Проверяем, есть ли у группы чат
    if not group.chat:
        # Создаем чат
        chat = Chat.objects.create(type="GROUP", name=group.name)
        group.chat = chat
        group.save()

        # Создаем UserChat для студентов группы
        for student in group.students.all():
            UserChat.objects.create(user=student, chat=chat, user_role="Student")

        # Если есть преподаватель, создаем UserChat для него
        if group.teacher_id:
            UserChat.objects.create(
                user=group.teacher_id, chat=chat, user_role="Teacher"
            )

        # Создаем UserChat для администраторов
        for admin in admins:
            if not UserChat.objects.filter(
                user=admin, chat=group.chat, user_role="Admin"
            ).exists():
                UserChat.objects.create(user=admin, chat=group.chat, user_role="Admin")

        return Response(status=status.HTTP_201_CREATED)
    else:
        user_chats = UserChat.objects.filter(chat=group.chat)
        for user_chat in user_chats:
            if (
                user_chat.user not in group.students.all()
                and user_chat.user != group.teacher_id
            ):
                user_chat.delete()  # Удаляем чаты для неактуальных студентов

        # Создаем UserChat для студентов
        for student in group.students.all():
            if not UserChat.objects.filter(user=student, chat=group.chat).exists():
                UserChat.objects.create(
                    user=student, chat=group.chat, user_role="Student"
                )

        # Создаем UserChat для преподавателя
        if (
            group.teacher_id
            and not UserChat.objects.filter(
                user=group.teacher_id, chat=group.chat
            ).exists()
        ):
            UserChat.objects.create(
                user=group.teacher_id, chat=group.chat, user_role="Teacher"
            )

        # Создаем UserChat для администраторов
        for admin in admins:
            if not UserChat.objects.filter(
                user=admin, chat=group.chat, user_role="Admin"
            ).exists():
                UserChat.objects.create(user=admin, chat=group.chat, user_role="Admin")

        return Response(status=status.HTTP_200_OK)
