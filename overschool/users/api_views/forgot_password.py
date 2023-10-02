from django.http import HttpResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser

from users.serializers.forgot_password_serializer import ForgotPasswordSerializer
from users.models import User
from users.services import JWTHandler, SenderServiceMixin
from common_services.mixins import WithHeadersViewSet


class ForgotPasswordView(WithHeadersViewSet, generics.GenericAPIView):
    """Endpoint for sending a new password by mail if the user has forgotten the old one
    <h2>/api/forgot_password/</h2>\n"""

    parser_classes = (MultiPartParser,)
    serializer_class = ForgotPasswordSerializer
    sender_service = SenderServiceMixin()
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(method='post', request_body=ForgotPasswordSerializer)
    @action(detail=False, methods=["POST"])
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        response = HttpResponse("/api/login/")

        email = serializer.validated_data["email"]
        user = User.objects.get(email=email)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response("User with this email does not exist.", status=404)

        # generation new password
        new_password = User.objects.make_random_password(length=11)

        # set new password
        user.set_password(new_password)
        user.save()

        # send message with new password
        self.sender_service.send_code_by_email(email=email)

        return Response("New password sent successfully. Check your email.")