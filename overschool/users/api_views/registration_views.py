import datetime

import jwt
from rest_framework import generics, permissions, response, status, views
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import User
from users.serializers import (
    ChangePasswordSerializer,
    FirstRegisterSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)
from users.services import RedisDataMixin, SenderServiceMixin, re_authentication


class RegisterView(generics.GenericAPIView, RedisDataMixin):
    """
    Эндпоинт регистрации юзера на платформе
    """

    serializer_class = UserSerializer
    queryset = User.objects.all()

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
            return Response({"status": "Error", "message": "Bad credentials"}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(generics.GenericAPIView):
    """
    Эндпоинт логина пользователя
    """

    serializer_class = LoginSerializer

    def post(self, request):

        serializer = LoginSerializer(request.data)
        if serializer.is_valid():
            email = serializer.email
            password = serializer.password

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

            response = Response(status=status.HTTP_201_CREATED)
            response.set_cookie(key="jwt", value=token, httponly=True)
            response.data = {"jwt": token}
            return response
        else:
            return Response(
                {"status": "Error", "message": f"{serializer.errors}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserView(APIView):
    """
    Эндпоинт для получения данных юзера
    """

    def get(self, request):
        token = request.COOKIES.get("jwt")

        if not token:
            raise AuthenticationFailed("Unauthenticated!")
        try:
            payload = jwt.decode(token, "secret", algorithm=["HS256"])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Unauthenticated!")

        user = User.objects.filter(user_id=payload["id"]).first()
        serializer = UserSerializer(user)
        return Response(serializer.data)


class UserApi(views.APIView):
    """
    Возможно, более лучшая версия похожей вьюхи
    """

    authentication_classes = (re_authentication.CustomUserReAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user

        serializer = UserSerializer(user)

        return response.Response(serializer.data)


class LogoutView(views.APIView):
    """
    Снова же более лучшая версия прошлой вьюхи
    """

    authentication_classes = (re_authentication.CustomUserReAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        resp = response.Response()
        resp.delete_cookie("jwt")
        resp.data = {"message": "so long farewell"}

        return resp


class ChangePasswordView(generics.UpdateAPIView):
    """
    An endpoint for changing password.
    """

    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = (IsAuthenticated,)

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            # set_password also hashes the password that the user will get
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            response = {
                "status": "success",
                "code": status.HTTP_200_OK,
                "message": "Password updated successfully",
                "data": [],
            }

            return Response(response)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SendInviteView(generics.GenericAPIView, SenderServiceMixin):
    """
    Эндпоинт для отправки приглашения со стороны админа
    """

    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)  # далее можно изменить

    def post(self, request):
        """
        Функция для отправки регистрационной ссылки пользоваелю, ответы требуют доработки
        """
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            sender_type = serializer.data["sender_type"]
            if sender_type == "mail":
                result = self.send_code_by_email(
                    serializer.data["recipient"], serializer.data["user_type"], serializer.data["course_id"]
                )
            else:
                result = self.send_code_by_phone(
                    serializer.data["recipient"], serializer.data["user_type"], serializer.data["course_id"]
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


class FirstTimeRegisterView(generics.GenericAPIView, SenderServiceMixin):
    """
    Эндпоинт на проверку валидности токена, по которому хочет зарегистрироваться пользователь
    """

    serializer_class = FirstRegisterSerializer
    queryset = User.objects.all()

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


class AdminForceRegistration(generics.GenericAPIView):
    """
    Эндпоинт регистрации пользователя админом (полной регистрации)
    """

    serializer_class = UserSerializer

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
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
            return Response({"status": "Error", "message": "Bad credentials"}, status=status.HTTP_400_BAD_REQUEST)
