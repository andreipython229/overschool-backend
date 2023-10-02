from common_services.mixins import WithHeadersViewSet
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.http import HttpResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from users.serializers import (
    PasswordResetSerializer,
    SignupSerializer,
)
from rest_framework import serializers
import random
import string
from users.services import JWTHandler
from overschool import settings
from django.contrib.auth.hashers import make_password

User = get_user_model()
jwt_handler = JWTHandler()


class SignupView(WithHeadersViewSet, generics.GenericAPIView):
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

        serializer.save()
        response = HttpResponse("/api/user/", status=201)
        return response


def generate_random_password(length=10):
    # Создаем строку, содержащую цифры и буквы в верхнем и нижнем регистре
    characters = string.ascii_letters + string.digits

    # Генерируем пароль с указанной длиной
    password = ''.join(random.choice(characters) for _ in range(length))

    return password


class SendPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class SendPasswordView(WithHeadersViewSet, generics.GenericAPIView):
    serializer_class = SendPasswordSerializer

    def post(self, request):
        email = request.data.get("email")

        # Генерируем пароль
        password = generate_random_password()

        # Создаем пользователя и устанавливаем ему пароль
        user = User(email=email)
        user.password = make_password(password)
        user.save()

        # Отправляем пароль на почту
        subject = "Your New Password"
        message = f"Your new password is: {password}"

        # Замените жестко закодированные значения на настройки из settings.py
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]

        try:
            send_mail(subject, message, from_email, recipient_list, auth_user=settings.EMAIL_HOST_USER,
                      auth_password=settings.EMAIL_HOST_PASSWORD)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "Password sent successfully"}, status=status.HTTP_200_OK)


class PasswordResetView(WithHeadersViewSet, generics.GenericAPIView):
    serializer_class = PasswordResetSerializer


    @swagger_auto_schema(method="post", request_body=PasswordResetSerializer)
    @action(detail=False, methods=["POST"])
    def send_reset_link(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        # Проверяем, существует ли пользователь с такой почтой
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response("User with this email does not exist.", status=404)

        # Отправляем код подтверждения на почту пользователя
        self.sender_service.send_code_by_email(email=email)

        return Response("Reset password link sent successfully.")

    @swagger_auto_schema(method="post", request_body=PasswordResetSerializer)
    @action(detail=False, methods=["POST"])
    def reset_password(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        new_password = serializer.validated_data["new_password"]

        # Проверяем, существует ли пользователь с такой почтой
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response("User with this email does not exist.", status=404)

        # Устанавливаем новый пароль и сохраняем пользователя
        user.set_password(new_password)
        user.save()
        return Response("Password reset successfully.")
