import json
import g4f

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from django.http import JsonResponse
from django.db.models import Max
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.views import APIView, View
from rest_framework.parsers import JSONParser

from users.models.user import User
from .models import UserMessage, BotResponse, OverAiChat, AIProvider
from .serializers import UserMessageSerializer, BotResponseSerializer, OverAiChatSerializer
from .schemas import OverAiChatSchemas, SendMessageToGPTSchema, LastMessagesSchema, LastTenChatsSchema


@method_decorator(csrf_exempt, name='dispatch')
class UserWelcomeMessageView(View):
    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            user.shown_welcome_message = True
            user.save()
            return JsonResponse({'message': 'show_welcome_message установлен в True'}, status=200)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Пользователь с указанным ID не найден'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
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
    parser_classes = [JSONParser]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, user_id):
        try:
            last_ten_chats = OverAiChat.objects.filter(user_id=user_id).annotate(max_id=Max('id')).order_by('-max_id')[:10]

            chat_data = {
                chat.id: chat.chat_name for chat in last_ten_chats
            }

            return JsonResponse(chat_data, safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(
    SendMessageToGPTSchema.send_message_schema(),
    name="post",
)
class SendMessageToGPT(APIView):
    parser_classes = [JSONParser]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            user_id = data.get('user_id', '')
            overai_chat_id = int(data.get('overai_chat_id', ''))
            messages = []

            past_messages = list(LastMessages.get(self, request, user_id, overai_chat_id))

            combined_data_str = past_messages[0].decode("utf-8")
            combined_data_list = json.loads(combined_data_str)

            for user_data, assistant_data in zip(combined_data_list[0][:4], combined_data_list[1][:4]):
                sender_question = user_data.get("sender_question", "")
                if sender_question:
                    messages.append({"role": "user", "content": sender_question})

                answer = assistant_data.get('answer', '')
                if answer:
                    messages.append({"role": "assistant", "content": answer})

            messages.append({"role": "user", "content": user_message})

            response = self.run_provider(messages)
            overai_chat = OverAiChat.objects.get(id=overai_chat_id)

            if not UserMessage.objects.filter(overai_chat_id=overai_chat_id).exists():
                overai_chat.chat_name = user_message
                overai_chat.save()
            UserMessage.objects.create(
                sender_id=user_id,
                sender_question=user_message,
                overai_chat_id=overai_chat
            )
            BotResponse.objects.create(
                sender_id=user_id,
                answer=response,
                overai_chat_id=overai_chat
            )
            return JsonResponse({'bot_response': response})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def run_provider(self, messages):
        try:
            providers = AIProvider.objects.all()
            for provider in providers:
                try:
                    response = g4f.ChatCompletion.create(
                        model=g4f.models.gpt_35_turbo_0613,
                        messages=messages,
                        provider=getattr(g4f.Provider, provider.name)
                    )
                    response_str = ''.join(response)
                    if response_str:
                        return response_str
                    else:
                        continue
                except Exception as e:
                    return f"Provider {provider.name} failed with exception: {e}"

            return "OVER AI Exception: No successful response from any provider"
        except Exception as e:
            return f"OVER AI Exception: {e}"


@method_decorator(
    LastMessagesSchema.last_messages_get_schema(),
    name="get"
)
class LastMessages(APIView):
    parser_classes = [JSONParser]

    def get(self, request, user_id, overai_chat_id):
        user = int(user_id)
        chat_id = int(overai_chat_id)
        try:
            latest_messages = UserMessage.objects.filter(sender_id=user, overai_chat_id=chat_id).order_by('-message_date')[:7]
            latest_responses = BotResponse.objects.filter(sender_id=user, overai_chat_id=chat_id).order_by('-message_date')[:7]
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
    parser_classes = [JSONParser]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        user_id = request.data['user_id']

        user = User.objects.get(id=user_id)
        new_chat = OverAiChat.objects.create(user_id=user)

        return JsonResponse({'overai_chat_id': new_chat.id}, status=200)


@method_decorator(
    OverAiChatSchemas.delete_chats_schema(),
    name="post"
)
class DeleteChatsView(APIView):
    parser_classes = [JSONParser]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, user_id):
        try:
            # Получаем чаты пользователя по его ID и удаляем те, у которых название 'Новый чат'
            OverAiChat.objects.filter(user_id=user_id, chat_name='Новый чат').delete()
            return JsonResponse({'message': 'Чаты успешно удалены'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
