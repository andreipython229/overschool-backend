from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import AllowAny
from schools.models import School
from transliterate import translit
from users.serializers import SignupSchoolOwnerSerializer
from users.services import SenderServiceMixin

from ..models.utm_label import UtmLabel

sender_service = SenderServiceMixin()
User = get_user_model()


class SignupSchoolOwnerView(LoggingMixin, WithHeadersViewSet, generics.GenericAPIView):
    """Ендпоинт регистрации владельца школы\n
    <h2>/api/register-school-owner/</h2>\n
    Ендпоинт регистрации владельца школы,
    или же дополнение или изменения
    необходимых данных уже зарегистрированного пользователя,
    для регистрации школы"""

    permission_classes = [AllowAny]
    serializer_class = SignupSchoolOwnerSerializer

    def post(self, request, *args, **kwargs):
        utm_source = request.data.get("utm_source", None)
        utm_medium = request.data.get("utm_medium", None)
        utm_campaign = request.data.get("utm_campaign", None)
        utm_term = request.data.get("utm_term", None)
        utm_content = request.data.get("utm_content", None)
        referral_code = kwargs.get("referral_code")

        email = request.data.get("email")
        phone_number = request.data.get("phone_number")
        school_name = translit(request.data.get("school_name"), "ru", reversed=True)
        if not all([email, phone_number, school_name]):
            return HttpResponse(
                "Требуется указать email, номер телефона и название школы", status=400
            )

        if email and User.objects.filter(email=email).exists():
            return HttpResponse("Email уже существует.", status=400)

        if School.objects.filter(name=school_name).exists():
            return HttpResponse("Название школы уже существует.", status=400)

        serializer = self.get_serializer(
            data=request.data, context={"referral_code": referral_code}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Отправка уведомления о успешной регистрации и создании школы
        domain = self.request.META.get("HTTP_X_ORIGIN")
        url = f"{domain}/login/"
        subject = "Успешная регистрация"
        message = f"Вы успешно зарегистрированы, ваша школа '{school_name}'создана.Перейдите по ссылке для ознакомления {url}"

        send = sender_service.send_code_by_email(
            email=email, subject=subject, message=message
        )

        new_user = get_object_or_404(User, email=email)

        UtmLabel.objects.create(
            user=new_user,
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
            utm_term=utm_term,
            utm_content=utm_content,
        )

        if send and send["status_code"] == 500:
            return HttpResponse(send["error"], status=send["status_code"])

        return HttpResponse("/api/user/", status=201)
