import json
import g4f

from django.http import JsonResponse
from drf_yasg import openapi
from django.views.decorators.http import require_POST
from drf_yasg.utils import swagger_auto_schema

from .models import GptMessage
from .serializers import GptMessageSerializer


@require_POST
@swagger_auto_schema(
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        operation_description="Send a message to chatgpt",
        tags=["ChatGPT"],
        properties={
            'message': openapi.Schema(type=openapi.TYPE_STRING),
            'user_id': openapi.Schema(type=openapi.TYPE_STRING),
        }
    ),
    responses={200: 'OK', 500: 'Internal Server Error'},
)
def send_message_to_gpt(request):
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
        user_id = data.get('user_id', '')

        response = run_provider(user_message)

        GptMessage.objects.create(
            sender_id=user_id,
            sedner_question=user_message,
            answer=response
        )

        return JsonResponse({'bot_response': response})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def run_provider(message: str):
    try:
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_35_turbo_0613,
            messages=[{
                "role": "user",
                "content": message
            }],
            provider=g4f.Provider.You,
            stream=True
        )
        response_str = ''.join(response)
        return response_str
    except Exception as e:
        return f"ChatGPT Exception: {e}"


@swagger_auto_schema(
    operation_description="Get the user's last 10 messages",
    tags=["ChatGPT"],
    manual_parameters=[
        openapi.Parameter('user_id', in_=openapi.IN_PATH, type=openapi.TYPE_STRING),
    ],
    responses={200: GptMessageSerializer(many=True), 500: 'Internal Server Error'},
)
def last_10_messages(request, user_id):
    user = user_id
    try:
        latest_messages = Message.objects.filter(sender_id=user).order_by('-date')[:10]
        serializer = GptMessageSerializer(latest_messages, many=True)
        return JsonResponse(serializer.data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
