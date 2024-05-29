import json
import g4f
from g4f.client import Client

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from django.http import JsonResponse
from django.db.models import Max, Window, F, Count, Q
from django.db.models.functions import RowNumber
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.views import APIView, View
from rest_framework.parsers import JSONParser

from users.models.user import User
from .models import UserMessage, BotResponse, OverAiChat, AIProvider
from .serializers import UserMessageSerializer, BotResponseSerializer, OverAiChatSerializer
from .schemas import OverAiChatSchemas, SendMessageToGPTSchema, LastMessagesSchema, LastTenChatsSchema


class AssignChatOrderView(APIView):
    """
    Назначение порядка чатов пользователя
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        try:
            # Получаем данные о порядке чатов из запроса
            chat_data = request.data

            # Обновляем порядок чатов в базе данных
            for chat_id, chat_info in chat_data.items():
                # Получаем объект чата по его id
                chat = OverAiChat.objects.get(id=chat_id)
                # Обновляем порядковый номер чата
                chat.order = chat_info['order']
                chat.save()

            return JsonResponse({'success': True}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class UserWelcomeMessageView(View):
    """
    Приветственное сообщение в OVER AI:
    - Было ли оно показано для конкретного пользователя или нет
    - Обновление состояния на True, если не было показано приветственное сообщение
    """

    def post(self, request):
        try:
            user = request.user
            user.shown_welcome_message = True
            user.save()
            return JsonResponse({'message': 'show_welcome_message установлен в True'}, status=200)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Пользователь с указанным ID не найден'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def get(self, request):
        try:
            user = request.user
            show_welcome_message = user.shown_welcome_message
            return JsonResponse({'show_welcome_message': show_welcome_message})
        except User.DoesNotExist:
            return JsonResponse({'error': 'Пользователь с указанным ID не найден'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(
    LastTenChatsSchema.last_ten_chats_get_schema(),
    name="get",
)
class LastTenChats(APIView):
    """
    Получение последних 10 чатов для пользователя
    """

    parser_classes = [JSONParser]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        try:
            user = request.user
            last_ten_chats = OverAiChat.objects.filter(user_id=user, order__gte=1, order__lte=10).order_by('order')[:10]

            chat_data = {
                chat.id: {
                    'order': chat.order,
                    'chat_name': chat.chat_name
                } for chat in last_ten_chats
            }

            return JsonResponse(chat_data, safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(
    SendMessageToGPTSchema.send_message_schema(),
    name="post",
)
class SendMessageToGPT(APIView):
    """
    Отправление сообщения в OVER AI
    """

    parser_classes = [JSONParser]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        try:
            # Получаем данные из request
            data = json.loads(request.body)
            user_message = data.get('message', '')
            language = data.get('language', '')
            user = request.user.id
            overai_chat_id = data.get('overai_chat_id', '')
            messages = []

            # Получаем последние сообщения для конкретного чата
            past_messages = list(LastMessages.get(self, request, overai_chat_id))

            # Декодируем последние сообщения
            combined_data_str = past_messages[0].decode("utf-8")
            combined_data_list = json.loads(combined_data_str)

            # Передача последних сообщений для OVER AI, для поддержки контекста
            for user_data, assistant_data in zip(combined_data_list[0][:4], combined_data_list[1][:4]):
                sender_question = user_data.get("sender_question", "")
                if sender_question:
                    messages.append({"role": "user", "content": sender_question})

                answer = assistant_data.get('answer', '')
                if answer:
                    messages.append({"role": "assistant", "content": answer})

            messages.append({"role": "user", "content": user_message})

            # Запускаем получение ответа от провайдеров
            response = self.run_provider(messages, language)
            overai_chat = OverAiChat.objects.get(id=overai_chat_id)

            if not UserMessage.objects.filter(overai_chat_id=overai_chat_id).exists():
                overai_chat.chat_name = user_message
                overai_chat.save()

            UserMessage.objects.create(
                sender_id=user,
                sender_question=user_message,
                overai_chat_id=overai_chat
            )

            BotResponse.objects.create(
                sender_id=user,
                answer=response,
                overai_chat_id=overai_chat
            )
            return JsonResponse({'bot_response': response})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def run_provider(self, messages, language):
        """
        Получение ответа от провайдера
        """

        if language == 'ENG':
            system_message = {"role": "user", "content": "Please respond only in English."}
            messages.append(system_message)
        else:
            system_message = {"role": "user", "content": "Отвечай только на русском языке."}
            messages.append(system_message)

        try:
            response = Client().chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )

            response_str = ''.join(response.choices[0].message.content)
            if response_str:
                return response_str
            else:
                return "Ошибка: нет подходящего ответа, попробуйте еще раз"
        except Exception:
            return "Ошибка: нет подходящего ответа, попробуйте еще раз"


@method_decorator(
    LastMessagesSchema.last_messages_get_schema(),
    name="get"
)
class LastMessages(APIView):
    """
    Получение последних сообщений от пользователя и ответов от OVER AI для конкретного чата
    """

    parser_classes = [JSONParser]

    def get(self, request, overai_chat_id):
        user = request.user
        try:
            latest_messages = UserMessage.objects.filter(sender_id=user, overai_chat_id=overai_chat_id).order_by(
                '-message_date')[:7]
            latest_responses = BotResponse.objects.filter(sender_id=user, overai_chat_id=overai_chat_id).order_by(
                '-message_date')[:7]
            user_serializer = UserMessageSerializer(latest_messages, many=True)
            bot_serializer = BotResponseSerializer(latest_responses, many=True)

            combined_data = list(reversed(user_serializer.data)), list(reversed(bot_serializer.data))

            return JsonResponse(combined_data, safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(
    OverAiChatSchemas.create_chat_schema(),
    name="post"
)
class CreateChatView(APIView):
    """
    Создание чата пользователя
    """

    parser_classes = [JSONParser]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        user = request.user
        new_chat = OverAiChat.objects.create(user_id=user)
        order = 2

        last_10_chats = OverAiChat.objects.filter(user_id=user).exclude(id=new_chat.id).order_by('-order')[:10][::-1]

        for chat in last_10_chats:
            chat.order = order
            chat.save()
            order += 1

        new_chat.order = 1
        new_chat.save()

        new_last_10_chats = OverAiChat.objects.filter(user_id=user, order__range=(1, 10)).order_by('-order')

        # Устанавливаем порядковый номер 0 для всех остальных чатов пользователя, не включенных в последние 10
        OverAiChat.objects.filter(user_id=user).exclude(id__in=[chat.id for chat in new_last_10_chats]).update(order=0)

        return JsonResponse({'overai_chat_id': new_chat.id}, status=200)


class DeleteChatView(APIView):
    """
    Удаление чата пользователя
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        try:
            user = request.user
            chat_id = request.data.get('chat_id')
            chat_list = request.data.get('orderData')
            cleaned_order_data = [chat_data for chat_data in chat_list if chat_data.get('id') != chat_id]
            sorted_cleaned_order_data = sorted(cleaned_order_data, key=lambda x: x['order'])

            if not OverAiChat.objects.filter(id=chat_id).exists():
                return JsonResponse({'error': 'Чат с указанным ID не найден'}, status=404)

            UserMessage.objects.filter(overai_chat_id=chat_id).delete()
            BotResponse.objects.filter(overai_chat_id=chat_id).delete()
            OverAiChat.objects.filter(id=chat_id).delete()

            # Устанавливаем 0 для всех чатов
            OverAiChat.objects.filter(user_id=user.id).update(order=0)

            # Присваиваем им новые значения от 1 до 9
            new_order = 1
            for chat_data in sorted_cleaned_order_data:
                chat_id = chat_data.get('id')

                # Установка нового порядка чата
                OverAiChat.objects.filter(id=chat_id).update(order=new_order)
                new_order += 1

            order_data_ids = [chat_data.get('id') for chat_data in chat_list]
            latest_chat = OverAiChat.objects.filter(user_id=user.id).exclude(id__in=order_data_ids).order_by(
                '-id').first()

            if latest_chat:
                latest_chat.order = 10
                latest_chat.save()

            return JsonResponse({'message': 'Чат успешно удален'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
