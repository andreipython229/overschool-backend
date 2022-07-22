import datetime

import jwt
from rest_framework import permissions, status, views, viewsets
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import SchoolUser
from users.serializers import RegisterSerializer, SchoolUserSerializer
from users.services import RedisDataMixin, SenderServiceMixin

from users.models import User
from users.serializers import RegisterSerializer, UserSerializer
from users.services import RedisDataMixin, SenderServiceMixin


class RegisterView(APIView, RedisDataMixin):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        data = self._get_data_token(request.data.get("token"))
        if serializer.is_valid() and data and data["status"]:
            serializer.save()

            return Response(
                {
                    "status": "OK",
                    "message": "User created successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response({"status": "Error", "message": "Bad credentials"})


class LoginView(APIView):
    def post(self, request):
        email = request.data["email"]
        password = request.data["password"]

        user = User.objects.filter(email=email).first()

        if user is None:
            raise AuthenticationFailed("User not found!")

        if not user.check_password(password):
            raise AuthenticationFailed("Incorrect password!")

        payload = {
            "id": user.id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            "iat": datetime.datetime.utcnow(),
        }

        token = jwt.encode(payload, "secret", algorithm="HS256").decode("utf-8")

        response = Response()

        response.set_cookie(key="jwt", value=token, httponly=True)
        response.data = {"jwt": token}
        return response


class UserView(APIView):
    def get(self, request):
        token = request.COOKIES.get("jwt")

        if not token:
            raise AuthenticationFailed("Unauthenticated!")

        try:
            payload = jwt.decode(token, "secret", algorithm=["HS256"])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Unauthenticated!")

        user = User.objects.filter(id=payload["id"]).first()
        serializer = UserSerializer(user)
        return Response(serializer.data)


class LogoutView(APIView):
    def post(self, request):
        response = Response()
        response.delete_cookie("jwt")
        response.data = {"status": "OK", "message": "User Log out"}
        return response


class RegisterAdminView(views.APIView, SenderServiceMixin):
    """
    Вьюха для регистрации со стороны админа
    """

    permission_classes = (permissions.AllowAny,)  # далее можно изменить

    def post(self, request):
        """
        Функция для отправки регистрационной ссылки пользоваелю, ответы требуют доработки
        """
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            sender_type = serializer["sender_type"]
            if sender_type == "mail":
                result = self.send_code_by_email(
                    serializer["recipient"], serializer["user_type"]
                )
            else:
                result = self.send_code_by_phone(
                    serializer["recipient"], serializer["user_type"]
                )
            if result:
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
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"status": "Error", "error": "no_data"},
                status=status.HTTP_400_BAD_REQUEST,
            )
