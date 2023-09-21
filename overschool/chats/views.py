from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, serializers, status, generics
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg import openapi
from .constants import CustomResponses
from .models import Chat, Message, UserChat
from .request_params import ChatParams, UserParams
from .schemas import ChatSchemas
from .serializers import ChatSerializer, MessageSerializer, ChatInfoSerializer

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

        serializer = ChatSerializer(chats, many=True, context={'request': self.request})

        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses=ChatSchemas.chat_uuid_schema,
        manual_parameters=[UserParams.user_id],
        operation_description="Get or create chat with user",
        operation_summary="Get or create chat with user",
        tags=["chats"],
    )
    def post(self, request, *args, **kwargs):
        chat_creator = self.request.user

        chat_reciever_id = request.data.get("user_id")
        chat_reciever = is_user_exist(chat_reciever_id)
        if chat_reciever is False:
            return Response(
                {"error": "User does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )

        existed_chat_id = UserChat.get_existed_chat_id(chat_creator, chat_reciever)
        if existed_chat_id:
            existed_chat = Chat.objects.get(id=existed_chat_id)
            user_chat_serializer = ChatSerializer(existed_chat, context={'request': self.request})
            return Response(user_chat_serializer.data, status=status.HTTP_200_OK)
        else:
            chat = Chat.objects.create()
            UserChat.objects.create(user=chat_creator, chat=chat)
            UserChat.objects.create(user=chat_reciever, chat=chat)

            existed_chat_id = UserChat.get_existed_chat_id(chat_creator, chat_reciever)
            if existed_chat_id:
                existed_chat = Chat.objects.get(id=existed_chat_id)
                user_chat_serializer = ChatSerializer(existed_chat, context={'request': self.request})
                return Response(
                    user_chat_serializer.data, status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {"error": "Chat does not created"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

    @action(detail=False, methods=['POST'])
    @swagger_auto_schema(
        responses=ChatSchemas.chat_uuid_schema,
        manual_parameters=[
            openapi.Parameter(
                'teacher_id',
                openapi.IN_QUERY,
                description='ID учителя',
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                'student_id',
                openapi.IN_QUERY,
                description='ID ученика',
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                'message',
                openapi.IN_QUERY,
                description='Сообщение для чата',
                type=openapi.TYPE_STRING,
                required=False,  # Установите на True, если параметр обязателен
            ),
        ],
        operation_description="Get or create chat with user",
        operation_summary="Get or create chat with user",
        tags=["chats"])
    def create_personal_chat(self, request):
        teacher_id = request.data.get('teacher_id')
        student_id = request.data.get('student_id')
        message = request.data.get('message', '')  # Если сообщение не передано, оставляем пустым

        # Валидация и проверка существования учителя и ученика
        teacher = User.objects.filter(id=teacher_id, groups__name="Teacher", school=request.user.school).first()
        student = User.objects.filter(id=student_id, groups__name="Student", school=request.user.school).first()

        if not teacher or not student:
            return Response({'detail': 'Неверные идентификаторы учителя и/или ученика.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Создаем чат
        chat = Chat.objects.create()

        # Добавляем учителя и ученика в чат
        UserChat.objects.create(user=teacher, chat=chat)
        UserChat.objects.create(user=student, chat=chat)

        # Если передано сообщение, создаем первое сообщение в чате
        if message:
            Message.objects.create(chat=chat, sender=teacher, content=message)

        return Response({'detail': 'Персональный чат успешно создан.'}, status=status.HTTP_201_CREATED)


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

        serializer = ChatSerializer(chat, context={'request': self.request})

        return Response(serializer.data, status=status.HTTP_200_OK)

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
        serializer = ChatSerializer(chat, context={'request': self.request})

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
        serializer = MessageSerializer(messages, many=True, context={'request': self.request})

        return Response(serializer.data, status=status.HTTP_200_OK)


class ChatListInfo(LoggingMixin, WithHeadersViewSet, generics.ListAPIView):
    """
    - Список всех чатов для текущего пользователя с непрочитанными сообщениями
    """

    serializer_class = ChatInfoSerializer
    parser_classes = (MultiPartParser,)
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_queryset(self):
        user = self.request.user
        chats_for_user = UserChat.objects.filter(user=user)
        chats_list = [str(chat.chat) for chat in chats_for_user]
        queryset = Chat.objects.filter(id__in=chats_list)
        return queryset

    def get_total_unread(self):
        user = self.request.user
        user_chats = Chat.objects.filter(userchat__user=user)
        total_unread = Message.objects.filter(chat__in=user_chats).exclude(read_by=user).count()
        return total_unread

    @swagger_auto_schema(
        operation_description="Get all chats info for user",
        operation_summary="Get all chats info for user",
        tags=["chats"],
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        total_unread = self.get_total_unread()
        total_unread_dict = {"total_unread": total_unread}
        result_list = [total_unread_dict] + serializer.data

        return Response(result_list)
