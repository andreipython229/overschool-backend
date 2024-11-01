import random
import string

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse
from django.template.loader import render_to_string
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
        if User.objects.filter(email__iexact=email).exists():
            return HttpResponse("User already exists")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()
        response = HttpResponse("/api/user/", status=201)
        return response


def generate_random_password(length=10):
    characters = string.ascii_letters + string.digits
    password = "".join(random.choice(characters) for _ in range(length))

    return password


class SendPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    patronymic = serializers.CharField(required=False)


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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get("email")
        first_name = serializer.validated_data.get("first_name")
        last_name = serializer.validated_data.get("last_name")
        patronymic = serializer.validated_data.get("patronymic")

        existing_user = User.objects.filter(email=email).first()
        if existing_user:
            return Response({"user_id": existing_user.id}, status=status.HTTP_200_OK)

        password = generate_random_password()

        user = User.objects.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            patronymic=patronymic,
            password=make_password(password),
        )

        # Отправка пароля на почту
        domain = self.request.META.get("HTTP_X_ORIGIN")
        url = f"{domain}/login/"
        subject = "Новый пароль"
        html_message = render_to_string(
            "new_user_notification.html", {"password": password, "url": url}
        )

        send = sender_service.send_code_by_email(
            email=email, subject=subject, message=html_message
        )

        if send and send["status_code"] == 500:
            return Response(send["error"], status=send["status_code"])
        return Response({"user_id": user.id}, status=status.HTTP_200_OK)


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
