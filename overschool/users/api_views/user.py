from common_services.mixins import LoggingMixin, WithHeadersViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.request import Request
from rest_framework.response import Response
from users.models import User
from users.permissions import OwnerUserPermissions
from users.serializers import RegisterAdminSerializer, UserSerializer
from users.services import SenderServiceMixin


class UserViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet, SenderServiceMixin):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [DjangoModelPermissions | OwnerUserPermissions]

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
