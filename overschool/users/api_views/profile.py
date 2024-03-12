import hashlib
from urllib.parse import urlencode

from common_services.apply_swagger_auto_schema import apply_swagger_auto_schema
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from users.models import Profile, User
from users.permissions import OwnerProfilePermissions
from users.serializers import UserProfileGetSerializer, UserProfileSerializer
from users.services import SenderServiceMixin

from overschool import settings

s3 = UploadToS3()


def generate_hash_token(user):
    user_info = f"{user.id}-{user.email}"
    token = hashlib.sha256(user_info.encode()).hexdigest()
    return token


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
        if getattr(self, "swagger_fake_view", False):
            return (
                Profile.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
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
        email = user.email
        if email != new_email:
            if User.objects.filter(email=new_email).exists():
                return Response(
                    "Пользователь с такой электронной почтой уже существует",
                    status=400,
                )
            token = generate_hash_token(user)
            reset_password_url = f"{settings.SITE_URL}/email-confirm/{token}/"
            email_params = {"from_email": new_email}
            reset_password_url_with_params = (
                f"{reset_password_url}?{urlencode(email_params)}"
            )
            subject = "Подтверждения электронной почты Overschool"
            message = (
                f"Ссылка для подтверждения электронной почты:<br>"
                f"<a href='{reset_password_url_with_params}'>{reset_password_url_with_params}</a><br><br>"
                "Если это письмо пришло вам по ошибке, просто проигнорируйте его."
            )
            send = self.sender_service.send_code_by_email(
                email=new_email, subject=subject, message=message
            )
            if send and send["status_code"] == 500:
                return Response(send["error"], status=send["status_code"])

        if "user" in request.data and "email" in request.data["user"]:
            del request.data["user"]["email"]
        elif "user.email" in request.data:
            del request.data["user.email"]

        serializer = UserProfileSerializer(instance, data=request.data)
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

        return Response(serialized_data, status=status.HTTP_200_OK)


ProfileViewSet = apply_swagger_auto_schema(tags=["profiles"])(ProfileViewSet)


class EmailValidateSerializer(serializers.Serializer):
    pass


class EmailValidateView(LoggingMixin, WithHeadersViewSet, generics.GenericAPIView):
    """
    API для валидации email
    <h2>/api/email-confirm/<str:token>/</h2>\n
    """

    parser_classes = (MultiPartParser,)
    serializer_class = EmailValidateSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(tags=["profiles"])
    @action(detail=False, methods=["GET"])
    def get(self, request, *args, **kwargs):
        user = request.user
        token = kwargs.get("token")
        expected_token = generate_hash_token(user)
        try:
            if token == expected_token:
                from_email = request.GET.get("from_email")
                if from_email:
                    user.email = from_email
                    user.save()
                else:
                    return Response("Токен не действителен", status=400)
                return Response("Токен действителен", status=200)
            else:
                return Response("Токен не действителен", status=400)
        except:
            return Response("Токен не действителен", status=400)
