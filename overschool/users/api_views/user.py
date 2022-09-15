from datetime import datetime

import jwt
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.decorators import permission_classes as permissions
from rest_framework.decorators import renderer_classes
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import (AllowAny, DjangoObjectPermissions,
                                        IsAuthenticated)
from rest_framework.request import Request
from rest_framework.response import Response

from users.models import User, UserRole
from users.serializers import (ChangePasswordSerializer,
                               FirstRegisterSerializer, LoginSerializer,
                               RegisterAdminSerializer, RegistrationSerializer,
                               UserSerializer)
from users.services import SenderServiceMixin


class RegisterView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer

    @action(["POST"], detail=False)
    def register_user(self, request):
        user = request.data.get("user", {})
        serializer = RegistrationSerializer(data=user)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        role = UserRole.objects.get(pk=request.data["group"])
        role.user_set.add(User.objects.get(pk=data.pk))
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    @action(methods=["POST"], detail=False)
    def login_view(self, request):
        user = request.data.get("user", {})
        serializer = LoginSerializer(data=user)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserViewSet(
    viewsets.GenericViewSet,
    SenderServiceMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(methods=["POST"], detail=False)
    def login_view(self, request):
        user = request.data.get("user", {})
        serializer = LoginSerializer(data=user)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=["POST"], detail=False)
    def register(self, request):
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
            return Response(
                {"status": "Error", "message": "Bad credentials"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(methods=["POST"], detail=False)
    def login(self, request: Request):

        username = request.data["username"]
        password = request.data["password"]

        user = User.objects.filter(username=username, password=password).first()

        if user is None:
            raise AuthenticationFailed("Пользователь не найден")

        if not user.check_password(password):
            raise AuthenticationFailed("Неверный пароль")

        payload = {
            "id": user.id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=300),
            "iat": datetime.datetime.utcnow(),
        }

        token = jwt.encode(payload, "secret", algorithm="HS256").decode("utf-8")

        response = Response()

        response.set_cookie(key="jwt", value=token, httponly=True)
        response.data = {"jwt": token}

        return response

    @action(methods=["POST"], detail=False)
    def logout(self, request):
        response = Response()
        response.delete_cookie("jwt")
        response.data = {"message": "Успешно"}
        return response

    @action(methods=["PATCH"], detail=False)
    def change_password(self, request: Request):
        user = self.request.user
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            if not user.check_password(serializer.data.get("old_password")):
                return Response(
                    {"old_password": ["Wrong password."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # set_password also hashes the password that the user will get
            user.set_password(serializer.data.get("new_password"))
            user.save()
            response = {
                "status": "success",
                "code": status.HTTP_200_OK,
                "message": "Password updated successfully",
                "data": [],
            }

            return Response(response)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["POST"], detail=False)
    def send_invite(self, request: Request):
        serializer = RegisterAdminSerializer(data=request.data)
        if serializer.is_valid():
            sender_type = serializer.data["sender_type"]
            if sender_type == "mail":
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

    @action(methods=["GET"], detail=False)
    def get_token(self, request: Request):
        token = request.COOKIES.get("jwt")

        if not token:
            raise AuthenticationFailed("Не прошедший проверку подлинности!")

        try:
            payload = jwt.decode(token, "secret", algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Не прошедший проверку подлинности!")

        user = User.objects.filter(id=payload["id"]).first()

        serializer = UserSerializer(user)
        return Response(serializer.data)

    @action(methods=["POST"], detail=False)
    def register_by_admin(self, request):
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
            return Response(
                {"status": "Error", "message": "Bad credentials"},
                status=status.HTTP_400_BAD_REQUEST,
            )
