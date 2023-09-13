from datetime import timedelta

from common_services.mixins import WithHeadersViewSet
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from users.serializers import (
    ConfirmationSerializer,
    PasswordResetSerializer,
    SignupSerializer,
)
from drf_yasg.utils import swagger_auto_schema
from django.core.mail import send_mail
from users.services import JWTHandler, SenderServiceMixin
from rest_framework.decorators import action

User = get_user_model()
jwt_handler = JWTHandler()
sender_service = SenderServiceMixin()  # Создаем экземпляр SenderServiceMixin


class SignupView(WithHeadersViewSet, generics.GenericAPIView):
    """Эндпоинт регистрации пользователя\n
    <h2>/api/register/</h2>\n
    Эндпоинт регистрации пользователя"""

    permission_classes = [permissions.AllowAny]
    serializer_class = SignupSerializer
    parser_classes = (MultiPartParser,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response = HttpResponse("/api/user/", status=201)
        return response


class ConfirmationView(WithHeadersViewSet, generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ConfirmationSerializer
    allowed_methods = ["POST"]  # Only allow the "POST" method
    parser_classes = (MultiPartParser,)

    def post(self, request, school_name=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["code"]
        email = serializer.validated_data.get("email")
        phone_number = serializer.validated_data.get("phone_number")

        # Проверка кода подтверждения и остальных данных

        saved_code = User.objects.filter(
            confirmation_code=code, is_active=False
        ).exists()

        if saved_code:
            # Код подтверждения совпадает, выполняем дополнительные проверки
            user = get_object_or_404(User, confirmation_code=code, is_active=False)

            is_valid_email = (
                User.objects.filter(email=email).exists() if email else False
            )
            is_valid_phone_number = (
                User.objects.filter(phone_number=phone_number).exists()
                if phone_number
                else False
            )

            if (email and is_valid_email) or (phone_number and is_valid_phone_number):
                # Почта или номер телефона совпадают с данными в базе

                user.is_active = True  # Устанавливаем статус активации пользователя
                user.confirmation_code = (
                    None  # Удаляем код подтверждения из модели пользователя
                )
                user.confirmation_code_created_at = (
                    timezone.now()
                )  # Устанавливаем время создания кода подтверждения
                user.save(
                    update_fields=[
                        "is_active",
                        "confirmation_code",
                        "confirmation_code_created_at",
                    ]
                )

                return Response(
                    "Confirmation code is valid. User authenticated successfully and activated."
                )
            else:
                return Response("Invalid email or phone number.", status=400)
        else:
            expiry_time = timezone.now() - timedelta(
                minutes=User.CONFIRMATION_CODE_EXPIRY_MINUTES
            )
            User.objects.filter(confirmation_code_created_at__lt=expiry_time).delete()
            return Response(
                "Invalid confirmation code. Please check the code or request a new one.",
                status=400,
            )


class PasswordResetView(WithHeadersViewSet, generics.GenericAPIView):
    serializer_class = PasswordResetSerializer
    sender_service = SenderServiceMixin()  # Создаем экземпляр SenderServiceMixin

    @swagger_auto_schema(method='post', request_body=PasswordResetSerializer)
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

    @swagger_auto_schema(method='post', request_body=PasswordResetSerializer)
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