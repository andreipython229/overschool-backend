from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from rest_framework import generics, permissions
from users.serializers import (
    ConfirmationSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
    SignupSerializer,
)
from users.services import JWTHandler, SenderServiceMixin

User = get_user_model()
jwt_handler = JWTHandler()
sender_service = SenderServiceMixin()  # Создаем экземпляр SenderServiceMixin


class SignupView(LoggingMixin, WithHeadersViewSet, generics.GenericAPIView):
    """Эндпоинт регистрации пользователя\n
    Эндпоинт регистрации пользователя"""

    permission_classes = [permissions.AllowAny]
    serializer_class = SignupSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        email = serializer.validated_data["email"]
        phone_number = serializer.validated_data["phone_number"]

        if email:
            # Отправляем код подтверждения по электронной почте
            sender_service.send_code_by_email(email)
        elif phone_number:
            # Отправляем код подтверждения на телефон

            sender_service.send_code_by_phone(phone_number)
        else:
            return HttpResponse("Email or phone number is required.", status=400)

        # Сохраняем код подтверждения и другие данные в Redis

        response = HttpResponse("/api/user/", status=201)
        return response


class ConfirmationView(LoggingMixin, WithHeadersViewSet, generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ConfirmationSerializer

    def post(self, request, school_name=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["code"]
        email = serializer.validated_data.get("email")
        phone_number = serializer.validated_data.get("phone_number")

        # Проверка кода подтверждения и остальных данных

        saved_code = sender_service.REDIS_INSTANCE.get(code)

        if saved_code and code == saved_code.decode():
            # Код подтверждения совпадает, выполняем дополнительные проверки

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

                user = self.get_user_from_request()  # Получаем пользователя из запроса

                user.is_active = True  # Устанавливаем статус активации пользователя
                user.save()

                return HttpResponse(
                    "Confirmation code is valid. User authenticated successfully and activated."
                )
            else:
                return HttpResponse("Invalid email or phone number.", status=400)
        else:
            return HttpResponse(
                "Invalid confirmation code. Please check the code or request a new one.",
                status=400,
            )


class PasswordResetView(LoggingMixin, WithHeadersViewSet, generics.GenericAPIView):
    """Эндпоинт сброса пароля\n
    <ul>
        <li>Отправляем код для сброса пароля по электронной почте или Отправляем код для сброса пароля на телефон</li>
        <li>Сохраняем код для сброса пароля и другие данные в Redis</li>
    </ul>"""

    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        phone_number = serializer.validated_data["phone_number"]

        if email:
            # Отправляем код для сброса пароля по электронной почте
            reset_code = sender_service.send_code_for_password_reset_by_email(email)
        elif phone_number:
            # Отправляем код для сброса пароля на телефон

            reset_code = sender_service.send_code_for_password_reset_by_phone_number(
                phone_number
            )
        else:
            return HttpResponse("Email or phone number is required.", status=400)

        # Сохраняем код для сброса пароля и другие данные в Redis

        response = HttpResponse("Password reset code has been sent.", status=200)
        return response


class PasswordResetConfirmView(
    LoggingMixin, WithHeadersViewSet, generics.GenericAPIView
):
    """Эндпоинт проверки кода для сброса пароля\n
    <ul>
        <li>Проверяем код для сброса пароля в Redis</li>
        <li>Обновляем пароль</li>
    </ul>"""

    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data["email"]
        serializer.validated_data["reset_code"]
        serializer.validated_data["new_password"]

        # Проверяем код для сброса пароля в Redis

        # Обновляем пароль

        return HttpResponse("Password has been reset.", status=200)
