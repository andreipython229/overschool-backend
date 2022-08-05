from datetime import datetime

import jwt
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.decorators import permission_classes as permissions
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from users.models import User
from users.permissions import IsSuperAdmin
from users.serializers import (
    ChangePasswordSerializer,
    FirstRegisterSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)
from users.services import RedisDataMixin, SenderServiceMixin, re_authentication


class UserViewSet(viewsets.GenericViewSet, SenderServiceMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser | IsSuperAdmin]

    @action(methods=["POST"], detail=False)
    @permissions([AllowAny])
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
            return Response({"status": "Error", "message": "Bad credentials"}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["POST"], detail=False)
    @permissions([AllowAny])
    def login(self, request: Request):

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

    @action(methods=["POST"], detail=False)
    @permissions([IsAuthenticated])
    def logout(self, request: Request):
        response = Response()
        response.delete_cookie("jwt")
        response.data = {"status": "OK", "message": "User Log out"}
        return response

    @action(methods=["PATCH"], detail=False)
    @permissions([IsAuthenticated])
    def change_password(self, request: Request):
        user = self.request.user
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            if not user.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
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
    @permissions([IsAdminUser])
    def send_invite(self, request: Request):
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

    @action(methods=["GET"], detail=False)
    @permissions([AllowAny])
    def get_token(self, request: Request):
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

    @action(methods=["POST"], detail=False)
    @permissions([IsAuthenticated, IsAdminUser])
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
            return Response({"status": "Error", "message": "Bad credentials"}, status=status.HTTP_400_BAD_REQUEST)
