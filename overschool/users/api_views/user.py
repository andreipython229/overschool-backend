from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, DjangoObjectPermissions,
                                        IsAuthenticated)
from rest_framework.request import Request
from rest_framework.response import Response

from users.models import User, UserRole
from users.serializers import ChangePasswordSerializer, UserSerializer, RegisterAdminSerializer
from users.services import SenderServiceMixin
from common_services.mixins import WithHeadersViewSet


class UserViewSet(WithHeadersViewSet, viewsets.ModelViewSet, SenderServiceMixin, ):
    queryset = User.objects.all()
    serializer_class = UserSerializer

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
