import base64

from common_services.apply_swagger_auto_schema import apply_swagger_auto_schema
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from django.http import HttpResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from users.models import Profile, User
from users.permissions import OwnerProfilePermissions
from users.serializers import (
    EmailValidateSerializer,
    UserProfileGetSerializer,
    UserProfileSerializer,
)
from users.services import SenderServiceMixin

s3 = UploadToS3()


class ProfileViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    """Эндпоинт просмотра и изменения Profile\n
    <h2>/api/profile/</h2>\n
    возвращаем только объекты пользователя, сделавшего запрос"""

    queryset = Profile.objects.all()
    serializer_class = UserProfileSerializer
    sender_service = SenderServiceMixin()
    permission_classes = [OwnerProfilePermissions]
    http_method_names = ["get", "put", "patch", "head"]

    def get_queryset(self):
        # Возвращаем только объекты пользователя, сделавшего запрос
        self.request.user.last_login = timezone.now()
        self.request.user.save()
        return Profile.objects.filter(user=self.request.user.id)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return UserProfileGetSerializer
        else:
            return UserProfileSerializer

    def list(self, request, *args, **kwargs):
        if self.request.user.is_anonymous:
            return HttpResponse(status=401)
        queryset = self.get_queryset()
        serializer = UserProfileGetSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = self.request.user
        new_email = request.data.get("user", {}).get("email")
        email_confirm = False
        email = user.email
        if email != new_email:
            if User.objects.filter(email=new_email).exists():
                return Response(
                    "Пользователь с такой электронной почтой уже существует",
                    status=400,
                )
            email_confirm = True
            encoded_email = base64.b64encode(new_email.encode("utf-8"))
            token = (
                default_token_generator.make_token(user)
                + "."
                + encoded_email.decode("utf-8")
            )
            subject = "Подтверждения электронной почты Overschool"
            message = f"Токен подтверждения электронной почты: {token}"
            send = self.sender_service.send_code_by_email(
                email=new_email, subject=subject, message=message
            )
            if send and send["status_code"] == 500:
                return Response(send["error"], status=send["status_code"])
        user.email = (None,)
        user.save()
        user_data = request.data
        user_data["user"]["email"] = email
        serializer = UserProfileSerializer(instance, data=user_data)
        serializer.is_valid(raise_exception=True)

        if request.FILES.get("avatar"):
            if instance.avatar:
                s3.delete_file(str(instance.avatar))
            serializer.validated_data["avatar"] = s3.upload_avatar(
                request.FILES["avatar"], instance.user.id
            )
        else:
            serializer.validated_data["avatar"] = instance.avatar

        serializer.save()

        serialized_data = UserProfileGetSerializer(instance).data
        serialized_data["email_confirm"] = email_confirm

        return Response(serialized_data, status=status.HTTP_200_OK)


ProfileViewSet = apply_swagger_auto_schema(tags=["profiles"])(ProfileViewSet)


class EmailValidateView(LoggingMixin, WithHeadersViewSet, generics.GenericAPIView):
    """
    API для валидации email
    <h2>/api/email-confirm/</h2>\n
    """

    parser_classes = (MultiPartParser,)
    serializer_class = EmailValidateSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        tags=["profiles"], method="post", request_body=EmailValidateSerializer
    )
    @action(detail=False, methods=["POST"])
    def post(self, request):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        token_parts = token.split(".")
        email = base64.b64decode(token_parts[1]).decode("utf-8")

        if default_token_generator.check_token(user, token_parts[0]):
            user.email = email
            user.save()
            return Response("Электронная почта успешно подтверждена", status=200)
        else:
            return Response("Token is invalid", status=400)
