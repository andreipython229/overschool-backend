import logging

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from schools.models import School
from transliterate import translit
from users.serializers import CreateSchoolSerializer, SignupSchoolOwnerSerializer
from users.services import SenderServiceMixin

from ..models.utm_label import UtmLabel
from ..services.create_school import create_school_for_user

logger = logging.getLogger(__name__)
sender_service = SenderServiceMixin()
User = get_user_model()


class SignupSchoolOwnerView(LoggingMixin, WithHeadersViewSet, generics.GenericAPIView):
    """
    Ендпоинт регистрации владельца школы ИЛИ создания новой школы существующим пользователем.
    <h2>/api/register-school-owner/</h2>
    """

    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if getattr(self, "request", None) and self.request.method == "POST":
            if self.request.user and self.request.user.is_authenticated:
                return CreateSchoolSerializer
            else:
                return SignupSchoolOwnerSerializer
        return SignupSchoolOwnerSerializer

    def post(self, request, *args, **kwargs):
        utm_source = request.data.get("utm_source", None)
        utm_medium = request.data.get("utm_medium", None)
        utm_campaign = request.data.get("utm_campaign", None)
        utm_term = request.data.get("utm_term", None)
        utm_content = request.data.get("utm_content", None)
        referral_code = kwargs.get("referral_code")

        if request.user and request.user.is_authenticated:
            user = request.user
            serializer = CreateSchoolSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            school_name = serializer.validated_data.get("school_name")
            phone_number = serializer.validated_data.get("phone_number")

            try:
                school = create_school_for_user(
                    user=user,
                    school_name=school_name,
                    phone_number=phone_number,
                    referral_code=referral_code,
                )
                domain = self.request.META.get("HTTP_X_ORIGIN")
                url = f"{domain}/login/"
                subject = "Успешная регистрация"
                message = f"Вы успешно зарегистрированы, ваша школа '{school.name}' создана. Перейдите по ссылке для входа: {url}"
                sender_service.send_code_by_email(
                    email=user.email, subject=subject, message=message
                )

                try:
                    html_message_template = render_to_string("register_user.html")
                    sender_service.send_code_by_email(
                        email=user.email,
                        subject="Спасибо за регистрацию на CourseHub!",
                        message=html_message_template,
                    )

                    html_message_template_d1 = render_to_string("day1.html")
                    sender_service.send_code_by_email(
                        email=user.email,
                        subject="День первый: CourseHub",
                        message=html_message_template_d1,
                    )
                except Exception as mail_e:
                    logger.error(
                        f"Error sending welcome emails to {user.email}: {mail_e}",
                        exc_info=True,
                    )
                return Response(
                    {
                        "message": f"Школа '{school.name}' успешно создана для пользователя {user.email}."
                    },
                    status=status.HTTP_201_CREATED,
                )
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(
                    f"Error creating school for authenticated user {user.email}: {e}",
                    exc_info=True,
                )
                return Response(
                    {"error": "Не удалось создать школу."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        else:

            serializer = SignupSchoolOwnerSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            try:
                user = serializer.save()
            except serializers.ValidationError:
                raise
            except Exception as e:
                logger.error(
                    f"Error during user find/create in serializer: {e}", exc_info=True
                )
                return Response(
                    {"error": "Ошибка при обработке данных пользователя."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            school_name = serializer.validated_data.get("school_name")
            phone_number = serializer.validated_data.get("phone_number")

            if not user or not school_name or not phone_number:
                return Response(
                    {
                        "error": "Не удалось получить все данные для создания школы после обработки пользователя."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                school = create_school_for_user(
                    user=user,
                    school_name=school_name,
                    phone_number=phone_number,
                    referral_code=referral_code,
                )

                domain = self.request.META.get("HTTP_X_ORIGIN")
                url = f"{domain}/login/"
                subject = "Успешная регистрация"
                message = f"Вы успешно зарегистрированы, ваша школа '{school.name}' создана. Перейдите по ссылке для входа: {url}"
                sender_service.send_code_by_email(
                    email=user.email, subject=subject, message=message
                )

                try:
                    html_message_template = render_to_string("register_user.html")
                    sender_service.send_code_by_email(
                        email=user.email,
                        subject="Спасибо за регистрацию на CourseHub!",
                        message=html_message_template,
                    )

                    html_message_template_d1 = render_to_string("day1.html")
                    sender_service.send_code_by_email(
                        email=user.email,
                        subject="День первый: CourseHub",
                        message=html_message_template_d1,
                    )
                except Exception as mail_e:
                    logger.error(
                        f"Error sending welcome emails to {user.email}: {mail_e}",
                        exc_info=True,
                    )

                UtmLabel.objects.create(
                    user=user,
                    utm_source=utm_source,
                    utm_medium=utm_medium,
                    utm_campaign=utm_campaign,
                    utm_term=utm_term,
                    utm_content=utm_content,
                )

                return Response(
                    {
                        "message": f"Пользователь {user.email} и школа '{school.name}' успешно зарегистрированы."
                    },
                    status=status.HTTP_201_CREATED,
                )

            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(
                    f"Error creating school for new user {user.email}: {e}",
                    exc_info=True,
                )
                return Response(
                    {"error": "Не удалось создать школу."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
