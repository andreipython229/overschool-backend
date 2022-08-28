from datetime import datetime, timedelta

import jwt
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, renderer_classes
from rest_framework.decorators import permission_classes as permissions
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, DjangoModelPermissions, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from users.renderers import UserJSONRenderer
from users.models import User, UserRole
from users.serializers import (
    ChangePasswordSerializer,
    FirstRegisterSerializer,
    LoginSerializer,
    RegisterAdminSerializer,
    UserSerializer,
    RegistrationSerializer,
    LoginPrSerializer
)
from users.services import SenderServiceMixin


class RegisterView(viewsets.GenericViewSet, SenderServiceMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]
    renderer_classes = [UserJSONRenderer]

    @action(['POST'], detail=False)
    def register_user(self, request):
        print(request.data)
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        role = UserRole.objects.get(pk=request.data['group'])
        role.user_set.add(User.objects.get(pk=data.pk))
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginView(viewsets.GenericViewSet, SenderServiceMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = User.objects.all()
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    renderer_classes = [UserJSONRenderer]

    @action(methods=["POST"], detail=False)
    def login_view(self, request):
        user = request.data.get('user', {})
        serializer = LoginSerializer(data=request.data)
        role = UserRole.objects.all()
        print(serializer)
        for r in role:
            print(r.__dict__)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class UserViewSet(viewsets.GenericViewSet, SenderServiceMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]

    @action(methods=["POST"], detail=False)
    @permissions([AllowAny])
    @renderer_classes([UserJSONRenderer])
    def login_view(self, request):
        user = request.data.get('user', {})

        serializer = LoginSerializer(data=user)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

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

    @action(methods=["POST"], detail=False, permission_classes=[AllowAny])
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
                "exp": datetime.utcnow() + timedelta(minutes=60),
                "iat": datetime.utcnow(),
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

    @action(methods=["POST"], detail=False, permission_classes=[IsAuthenticated])
    def logout(self, request: Request):
        response = Response()
        response.delete_cookie("jwt")
        response.data = {"status": "OK", "message": "User Log out"}
        return response

    @action(methods=["PATCH"], detail=False, permission_classes=[IsAuthenticated])
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

    @action(methods=["POST"], detail=False, permission_classes=[IsAuthenticated])
    def send_invite(self, request: Request):
        serializer = RegisterAdminSerializer(data=request.data)
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

    @action(methods=["GET"], detail=False, permission_classes=[AllowAny])
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

    @action(methods=["POST"], detail=False, permission_classes=[IsAuthenticated])
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
