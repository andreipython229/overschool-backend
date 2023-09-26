from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.http import HttpResponse
from rest_framework import generics, permissions
from users.serializers import SignupSchoolOwnerSerializer
from users.services import JWTHandler

User = get_user_model()
jwt_handler = JWTHandler()


class SignupSchoolOwnerView(LoggingMixin, WithHeadersViewSet, generics.GenericAPIView):
    """Ендпоинт регистрации владельца школы\n
    <h2>/api/{school_name}/register-school-owner/</h2>\n
    Ендпоинт регистрации владельца школы,
    или же дополнение или изменения
    необходимых данных уже зарегистрированного пользователя,
    для регистрации школы"""

    permission_classes = [permissions.AllowAny]
    serializer_class = SignupSchoolOwnerSerializer

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        phone_number = request.data.get("phone_number")

        if not all([email, phone_number]):
            return HttpResponse("Email and phone number is required", status=400)

        if request.user.is_authenticated:
            user = self.request.user

            if not check_password(request.data.get("password"), user.password):
                return HttpResponse("Invalid password credentials", status=401)

            if user.email != email and User.objects.filter(email=email).exists():
                return HttpResponse("Email already exists.", status=400)

            if (
                user.phone_number != phone_number
                and User.objects.filter(phone_number=phone_number).exists()
            ):
                return HttpResponse("Phone number already exists.", status=400)

            serializer = self.get_serializer(user, data=request.data)
        else:
            if email and User.objects.filter(email=email).exists():
                return HttpResponse("Email already exists.", status=400)

            if phone_number and User.objects.filter(phone_number=phone_number).exists():
                return HttpResponse("Phone number already exists.", status=400)

            serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return HttpResponse("/api/user/", status=201)
