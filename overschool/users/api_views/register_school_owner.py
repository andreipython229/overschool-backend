import re

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import Group
from django.http import HttpResponse
from rest_framework import generics
from rest_framework.permissions import AllowAny
from schools.models import School, SchoolHeader, Tariff, TariffPlan
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

    permission_classes = [AllowAny]
    serializer_class = SignupSchoolOwnerSerializer

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        phone_number = request.data.get("phone_number")
        school_name = request.data.get("school_name")
        school_name = re.sub(r"[^A-Za-z0-9._-]", "", school_name)

        if not all([email, phone_number, school_name]):
            return HttpResponse(
                "Требуется указать email, номер телефона и название школы", status=400
            )

        if request.user.is_authenticated:
            user = self.request.user

            if School.objects.filter(owner=user).count() >= 2:
                return HttpResponse(
                    "Пользователь может быть владельцем только двух школ.", status=400
                )

            if not check_password(request.data.get("password"), user.password):
                return HttpResponse("Неверные учетные данные пароля", status=401)

            if user.email != email and User.objects.filter(email=email).exists():
                return HttpResponse("Email уже существует.", status=400)
            if School.objects.filter(name=school_name).exists():
                return HttpResponse("Название школы уже существует.", status=400)

            if (
                user.phone_number != phone_number
                and User.objects.filter(phone_number=phone_number).exists()
            ):
                return HttpResponse("Номер телефона уже существует.", status=400)
            school = School.objects.create(
                name=school_name,
                owner=user,
                tariff=Tariff.objects.get(name=TariffPlan.INTERN.value),
            )
            if school:
                SchoolHeader.objects.create(school=school, name=school.name)

            group = Group.objects.get(name="Admin")
            user.groups.create(group=group, school=school)
        else:
            if email and User.objects.filter(email=email).exists():
                return HttpResponse("Email уже существует.", status=400)

            if phone_number and User.objects.filter(phone_number=phone_number).exists():
                return HttpResponse("Номер телефона уже существует.", status=400)
            if School.objects.filter(name=school_name).exists():
                return HttpResponse("Название школы уже существует.", status=400)

            serializer = self.get_serializer(data=request.data)

            serializer.is_valid(raise_exception=True)
            serializer.save()

        return HttpResponse("/api/user/", status=201)
