from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.http import HttpResponse
from rest_framework import generics
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from schools.models import School, Tariff, TariffPlan
from users.serializers import SignupSchoolOwnerSerializer
from users.services import JWTHandler

User = get_user_model()
jwt_handler = JWTHandler()


@permission_classes([AllowAny])
class SignupSchoolOwnerView(LoggingMixin, WithHeadersViewSet, generics.GenericAPIView):
    """Ендпоинт регистрации владельца школы\n
    <h2>/api/{school_name}/register-school-owner/</h2>\n
    Ендпоинт регистрации владельца школы,
    или же дополнение или изменения
    необходимых данных уже зарегистрированного пользователя,
    для регистрации школы"""

    serializer_class = SignupSchoolOwnerSerializer

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        school_name = request.data.get("school_name")
        phone_number = request.data.get("phone_number")

        if not all([email, phone_number]):
            return HttpResponse("Email and phone number is required", status=400)

        if request.user.is_authenticated:
            user = self.request.user

            if not check_password(request.data.get("password"), user.password):
                return HttpResponse("Invalid password credentials", status=401)

            if user.email != email and User.objects.filter(email=email).exists():
                return HttpResponse("Email already exists.", status=400)
            if School.objects.filter(name=school_name).exists():
                return HttpResponse("School_name already exists.", status=400)

            if (
                    user.phone_number != phone_number
                    and User.objects.filter(phone_number=phone_number).exists()
            ):
                return HttpResponse("Phone number already exists.", status=400)
            School.objects.create(name=school_name, owner=user, tariff=Tariff.objects.get(name=TariffPlan.INTERN.value))
        else:
            if email and User.objects.filter(email=email).exists():
                return HttpResponse("Email already exists.", status=400)

            if phone_number and User.objects.filter(phone_number=phone_number).exists():
                return HttpResponse("Phone number already exists.", status=400)
            if School.objects.filter(name=school_name).exists():
                return HttpResponse("School_name already exists.", status=400)

            serializer = self.get_serializer(data=request.data)

            serializer.is_valid(raise_exception=True)
            serializer.save()

        return HttpResponse("/api/user/", status=201)
