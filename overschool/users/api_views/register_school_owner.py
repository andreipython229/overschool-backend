import re

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from rest_framework import generics
from rest_framework.permissions import AllowAny
from schools.models import School
from users.serializers import SignupSchoolOwnerSerializer
from users.services import JWTHandler, SenderServiceMixin

sender_service = SenderServiceMixin()
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

        if email and User.objects.filter(email=email).exists():
            return HttpResponse("Email уже существует.", status=400)

        if School.objects.filter(name=school_name).exists():
            return HttpResponse("Название школы уже существует.", status=400)

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Отправка уведомления о успешной регистрации и создании школы
        url = "https://overschool.by/login/"
        subject = "Успешная регистрация"
        message = f"Вы успешно зарегистрированы, ваша школа '{school_name}'создана.Перейдите по ссылке для ознакомления {url}"

        send = sender_service.send_code_by_email(
            email=email, subject=subject, message=message
        )

        if send and send["status_code"] == 500:
            return HttpResponse(send["error"], status=send["status_code"])

        return HttpResponse("/api/user/", status=201)
