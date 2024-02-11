import random
import string

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from users.serializers import PasswordChangeSerializer, SignupSerializer
from users.services import SenderServiceMixin

User = get_user_model()
sender_service = SenderServiceMixin()


class SignupView(LoggingMixin, WithHeadersViewSet, generics.GenericAPIView):
    """Эндпоинт регистрации пользователя\n
    <h2>/api/register/</h2>\n
    Эндпоинт регистрации пользователя"""

    permission_classes = [permissions.AllowAny]
    serializer_class = SignupSerializer
    parser_classes = (MultiPartParser,)

    def post(self, request):
        email = request.data.get("email")
        if User.objects.filter(email=email).exists():
            return HttpResponse("User already exists")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.save()

        response_data = {
            "user_id": user_id
        }
        return Response(response_data, status=201)


def generate_random_password(length=10):
    characters = string.ascii_letters + string.digits
    password = "".join(random.choice(characters) for _ in range(length))
    return password


class SendPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class SendPasswordView(LoggingMixin, WithHeadersViewSet, generics.GenericAPIView):
    serializer_class = SendPasswordSerializer

    def get_permissions(self, *args, **kwargs):
        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin").exists():
            return permissions
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def post(self, request):
        email = request.data.get("email")
        if User.objects.filter(email=email).exists():
            return HttpResponse("User already exists")
        # Генерируем пароль
        password = generate_random_password()

        # Создаем пользователя и устанавливаем ему пароль
        user = User(email=email)
        user.password = make_password(password)
        user.save()

        # Отправляем пароль на почту
        url = "https://overschool.by/login/"
        subject = "Новый пароль"
        message = f"Ваш новый пароль : {password}, перейдите по ссылке: {url}"

        send = sender_service.send_code_by_email(
            email=email, subject=subject, message=message
        )
        if send and send["status_code"] == 500:
            return Response(send["error"], status=send["status_code"])

        return Response(
            {"message": "Password sent successfully"}, status=status.HTTP_200_OK
        )


class PasswordChangeView(LoggingMixin, WithHeadersViewSet, generics.GenericAPIView):
    serializer_class = PasswordChangeSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(method="post", request_body=PasswordChangeSerializer)
    @action(detail=False, methods=["POST"])
    def change_password(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        new_password = serializer.validated_data["new_password"]

        # Устанавливаем новый пароль и сохраняем пользователя
        user.set_password(new_password)
        user.save()
        return Response("Password change successfully.")
