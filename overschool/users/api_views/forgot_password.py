from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.contrib.auth.tokens import default_token_generator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, serializers
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from users.models import User
from users.serializers import ForgotPasswordSerializer, PasswordResetSerializer
from users.services import SenderServiceMixin

from overschool import settings


class ForgotPasswordView(LoggingMixin, WithHeadersViewSet, generics.GenericAPIView):
    """
    API для отправки токена востановления пароля по почте, если пользователь забыл старый
    <h2>/api/forgot_password/</h2>\n
    """

    parser_classes = (MultiPartParser,)
    serializer_class = ForgotPasswordSerializer
    sender_service = SenderServiceMixin()
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(method="post", request_body=ForgotPasswordSerializer)
    @action(detail=False, methods=["POST"])
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                "Пользователя с таким электронным адресом не существует.", status=404
            )

        # Создаем токен для сброса пароля
        token = default_token_generator.make_token(user)

        # Отправляем ссылку для сбора пароля
        reset_password_url = f"{settings.SITE_URL}/token-validate/{user.id}/{token}/"
        subject = "Восстановление доступа к Overschool"
        message = (
            f"Ссылка для сброса пароля:<br>"
            f"<a href='{reset_password_url}'>{reset_password_url}</a><br><br>"
            "Если это письмо пришло вам по ошибке, просто проигнорируйте его."
        )
        send = self.sender_service.send_code_by_email(
            email=email, subject=subject, message=message
        )
        if send and send["status_code"] == 500:
            return Response(send["error"], status=send["status_code"])

        return Response(
            "Ссылка для сброса пароля была отправлена. Проверьте свою электронную почту."
        )


class TokenValidateSerializer(serializers.Serializer):
    pass


class TokenValidateView(LoggingMixin, WithHeadersViewSet, generics.GenericAPIView):
    """
    API для валидации токена
    <h2>/api/token-validate/<int:user_id>/<str:token>/</h2>\n
    """

    parser_classes = (MultiPartParser,)
    serializer_class = TokenValidateSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=["GET"])
    def get(self, request, user_id, token):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                "Пользователя с таким электронным адресом не существует.", status=404
            )
        try:
            if default_token_generator.check_token(user, token):
                return Response({"email": user.email}, status=200)
            else:
                return Response("Токен не действителен", status=400)
        except:
            return Response("Токен не действителен", status=400)


class PasswordResetView(LoggingMixin, WithHeadersViewSet, generics.GenericAPIView):
    """
    API для сброса пароля
    <h2>/api/password-reset/</h2>\n
    """

    parser_classes = (MultiPartParser,)
    serializer_class = PasswordResetSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(method="post", request_body=PasswordResetSerializer)
    @action(detail=False, methods=["POST"])
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        new_password = request.data.get("new_password")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                "Пользователя с таким электронным адресом не существует.", status=404
            )
        user.set_password(new_password)
        user.save()
        return Response("Пароль был успешно сброшен.")
