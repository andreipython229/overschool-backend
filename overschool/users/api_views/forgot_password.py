from common_services.mixins import LoggingMixin, WithHeadersViewSet
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from users.models import User
from users.serializers.forgot_password_serializer import ForgotPasswordSerializer
from users.services import SenderServiceMixin


class ForgotPasswordView(LoggingMixin, WithHeadersViewSet, generics.GenericAPIView):
    """Endpoint for sending a new password by mail if the user has forgotten the old one
    <h2>/api/forgot_password/</h2>\n"""

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
            return Response("User with this email does not exist.", status=404)

        # generation new password
        new_password = User.objects.make_random_password(length=11)

        # set new password
        user.set_password(new_password)
        user.save()

        # Отправляем пароль на почту
        subject = "Your New Password"
        message = f"Your new password is: {new_password}"

        # send message with new password
        send = self.sender_service.send_code_by_email(
            email=email, subject=subject, message=message
        )
        if send and send["status_code"] == 500:
            return Response(send["error"], status=send["status_code"])

        return Response("New password sent successfully. Check your email.")
