from rest_framework import generics, permissions, status, viewsets
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.request import Request
from rest_framework.response import Response

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from users.models import User
from users.permissions import OwnerUserPermissions
from users.serializers import (InviteSerializer, UserSerializer,
                               ValidTokenSerializer)
from users.services import RedisDataMixin, SenderServiceMixin


class UserViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [DjangoModelPermissions | OwnerUserPermissions]


class InviteView(generics.GenericAPIView, SenderServiceMixin, RedisDataMixin):
    """
    Эндпоинт для отправки приглашения со стороны админа
    """

    serializer_class = InviteSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request):
        """
        Функция для отправки регистрационной ссылки пользователю
        """
        users = request.data
        exceptions = []
        user_exceptions = []

        for user in users:

            serializer = InviteSerializer(data=user)
            if serializer.is_valid():
                try:
                    sender_type = serializer.data["sender_type"]

                    if sender_type == "email" and serializer.data["user_type"] == 1 \
                            or sender_type == "email" and serializer.data["user_type"] == 2 \
                            or sender_type == "email" and serializer.data["user_type"] == 3 \
                            or sender_type == "email" and serializer.data["user_type"] == 4:
                        result = self.send_code_by_email(
                            serializer.data["recipient"],
                            serializer.data["user_type"],
                            serializer.data["course_id"],
                            serializer.data["group_id"],
                        )
                    if sender_type == "email" and serializer.data["user_type"] == 5 \
                            or sender_type == "email" and serializer.data["user_type"] == 6:
                        result = self.send_code_by_email(
                            serializer.data["recipient"],
                            serializer.data["user_type"],
                        )
                    if sender_type == "phone" and serializer.data["user_type"] == 1 \
                            or sender_type == "phone" and serializer.data["user_type"] == 2 \
                            or sender_type == "phone" and serializer.data["user_type"] == 3 \
                            or sender_type == "phone" and serializer.data["user_type"] == 4:
                        result = self.send_code_by_phone(
                            serializer.data["recipient"],
                            serializer.data["user_type"],
                            serializer.data["course_id"],
                            serializer.data["group_id"],
                        )
                    if sender_type == "phone" and serializer.data["user_type"] == 5 \
                            or sender_type == "phone" and serializer.data["user_type"] == 6:
                        result = self.send_code_by_phone(
                            serializer.data["recipient"],
                            serializer.data["user_type"],
                        )
                    # except Exception as d:
                    #     exceptions.append(str(d))
                    #     user_exceptions.append(serializer.data["recipient"])
                    #     print(d, "''''''")

                    if result and serializer.data["user_type"] == 1 \
                            or result and serializer.data["user_type"] == 2 \
                            or result and serializer.data["user_type"] == 3 \
                            or result and serializer.data["user_type"] == 4:
                        self._save_data_to_redis(
                            serializer.data["recipient"],
                            serializer.data["user_type"],
                            serializer.data["course_id"],
                            serializer.data["group_id"],
                        )
                    if result and serializer.data["user_type"] == 5 \
                            or result and serializer.data["user_type"] == 6:
                        self._save_data_to_redis(
                            serializer.data["recipient"],
                            serializer.data["user_type"],
                        )
                # except Exception as e:
                #     exceptions.append(str(e))
                #     user_exceptions.append(serializer.data["recipient"])
                #     print(e, "lll")

                except Exception as e:
                    assert True
                    exceptions.append(str(e))
                    user_exceptions.append(serializer.data["recipient"])
                    continue
                    pass
                else:
                    continue
                finally:
                    print(len(exceptions))
                    # user_exceptions.append(serializer.data["recipient"])
                    continue

            else:
                return Response(
                    {"status": "Error", "message": f"{serializer.errors}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if not exceptions:
            return Response(
                {"status": "OK", "message": "Url was sent", "exception": exceptions},
                status=status.HTTP_200_OK,

            )
        else:
            return Response(
                {"status": "Error", "message": "Some problems with send url", "exception": exceptions,
                 "users": user_exceptions},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ValidTokenView(generics.GenericAPIView, SenderServiceMixin, RedisDataMixin):
    """
    Эндпоинт на проверку валидности токена, по которому хочет зарегистрироваться пользователь
    """

    serializer_class = ValidTokenSerializer
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]

    def post(self, request):
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
    permission_classes = [permissions.AllowAny]

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
            return Response(
                {"status": "Error", "message": "Bad credentials"},
                status=status.HTTP_400_BAD_REQUEST,
            )
