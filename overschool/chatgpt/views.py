import json
import g4f

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from django.http import JsonResponse
from django.views import View
from django.db.models import Max
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from users.models.user import User
from .models import UserMessage, BotResponse, OverAiChat
from .serializers import UserMessageSerializer, BotResponseSerializer, OverAiChatSerializer
from .schemas import send_message_schema, latest_messages_schema


class LastTenChats(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, user_id):
        try:
            last_ten_chats = OverAiChat.objects.filter(user_id=user_id).annotate(max_id=Max('id')).order_by('-max_id')[:10]

            chat_ids = [chat.id for chat in last_ten_chats]

            return JsonResponse(chat_ids, safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class SendMessageToGPT(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    @method_decorator(send_message_schema)
    def post(self, request):
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            user_id = data.get('user_id', '')
            overai_chat_id = int(data.get('overai_chat_id', ''))
            messages = []

            past_messages = list(LastTenMessages.get(self, request, user_id, overai_chat_id))

            combined_data_str = past_messages[0].decode("utf-8")
            combined_data_list = json.loads(combined_data_str)

            for user_data, assistant_data in zip(combined_data_list[0][:5], combined_data_list[1][:5]):
                sender_question = user_data.get("sender_question", "")
                if sender_question:
                    messages.append({"role": "user", "content": sender_question})

                answer = assistant_data.get('answer', '')
                if answer:
                    messages.append({"role": "assistant", "content": answer})

            messages.append({"role": "user", "content": user_message})

            response = self.run_provider(messages)
            overai_chat = OverAiChat.objects.get(id=overai_chat_id)

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
            response = g4f.ChatCompletion.create(
                model=g4f.models.gpt_35_turbo_0613,
                messages=messages,
                provider=g4f.Provider.You,
                stream=True
            )
            response_str = ''.join(response)
            return response_str
        except Exception as e:
            return f"ChatGPT Exception: {e}"


class LastTenMessages(View):
    @method_decorator(latest_messages_schema)
    def get(self, request, user_id, overai_chat_id):
        user = int(user_id)
        chat_id = int(overai_chat_id)
        try:
            latest_messages = UserMessage.objects.filter(sender_id=user, overai_chat_id=chat_id).order_by('-message_date')[:10]
            latest_responses = BotResponse.objects.filter(sender_id=user, overai_chat_id=chat_id).order_by('-message_date')[:10]
            user_serializer = UserMessageSerializer(latest_messages, many=True)
            bot_serializer = BotResponseSerializer(latest_responses, many=True)

            combined_data = list(reversed(user_serializer.data)), list(reversed(bot_serializer.data))

            return JsonResponse(combined_data, safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class CreateChatView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        user_id = json.loads(request.body.decode('utf-8'))
        user = User.objects.get(id=user_id)
        new_chat = OverAiChat.objects.create(user_id=user)

        return JsonResponse({'overai_chat_id': new_chat.id}, status=200)

    def get(self, request, *args, **kwargs):
        return JsonResponse({'message': 'Invalid request method'}, status=400)
