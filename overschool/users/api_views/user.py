from rest_framework import generics, mixins, status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from users.models import User, UserRole
from users.serializers import UserSerializer, InviteSerializer, ValidTokenSerializer
from users.services import SenderServiceMixin, RedisDataMixin
from common_services.mixins import WithHeadersViewSet, LoggingMixin


class UserViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.DjangoModelPermissions]


class InviteView(generics.GenericAPIView, SenderServiceMixin, RedisDataMixin):
    """
    Эндпоинт для отправки приглашения со стороны админа
    """
    serializer_class = InviteSerializer
    permission_classes = [permissions.DjangoModelPermissions]

    def post(self, request: Request):
        """
        Функция для отправки регистрационной ссылки пользователю
        """
        serializer = InviteSerializer(data=request.data)
        if serializer.is_valid():
            sender_type = serializer.data["sender_type"]
            if sender_type == "email":
                result = self.send_code_by_email(
                    serializer.data["recipient"],
                    serializer.data["user_type"],
                    serializer.data["course_id"],
                )
            else:
                result = self.send_code_by_phone(
                    serializer.data["recipient"],
                    serializer.data["user_type"],
                    serializer.data["course_id"],
                )
            if result:
                self._save_data_to_redis(
                    serializer.data["recipient"],
                    serializer.data["user_type"],
                    serializer.data["course_id"], )
                return Response(
                    {"status": "OK", "message": "Url was sent"},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"status": "Error", "message": "Some problems with send url"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            return Response(
                {"status": "Error", "message": f"{serializer.errors}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ValidTokenView(generics.GenericAPIView, SenderServiceMixin, RedisDataMixin):
    """
    Эндпоинт на проверку валидности токена, по которому хочет зарегистрироваться пользователь
    """
    serializer_class = ValidTokenSerializer
    queryset = User.objects.all()
    permission_classes = [permissions.DjangoModelPermissions]

    def get(self, request):
        """
        Отправка данных, которые оставил админ, при входе юзера на страницу регистрации
        """
        token = request.data.get("token")
        data = self._get_data_token(token)
        if data:
            return Response(
                {
                    "status": "OK",
                    "user_type": data["user_type"],
                    "token_status": data["status"],
                    "course": data["course"],
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"status": "Error", "error": "no_data"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserRegistration(generics.GenericAPIView, SenderServiceMixin, RedisDataMixin):
    """
    Эндпоинт регистрации пользователя админом
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.DjangoModelPermissions]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            self._delete_data_from_redis()
            return Response(
                {
                    "status": "OK",
                    "message": "User created successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response({"status": "Error", "message": "Bad credentials"},
                            status=status.HTTP_400_BAD_REQUEST)
