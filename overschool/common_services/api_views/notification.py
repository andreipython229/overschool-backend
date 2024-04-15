import base64

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from schools.models import PromoCode, School, Tariff
from users.models import UserSubscription

User = get_user_model()


class PaymentNotificationSerializer(serializers.Serializer):
    pass


class PaymentNotificationView(LoggingMixin, WithHeadersViewSet, APIView):
    permission_classes = [AllowAny]
    serializer_class = PaymentNotificationSerializer

    def post(self, request):
        try:
            auth_header = request.META["HTTP_AUTHORIZATION"]
            auth_type, auth_b64_string = auth_header.split(" ")
            auth_bytes = base64.b64decode(auth_b64_string)
            auth_string = auth_bytes.decode("utf-8")
            signature = auth_string.split(":")[1]
        except KeyError:
            # Если заголовок HTTP_AUTHORIZATION отсутствует
            return JsonResponse(
                {"error": "Отсутствует заголовок HTTP_AUTHORIZATION"}, status=400
            )
        except Exception as e:
            # Обработка других возможных ошибок
            return JsonResponse({"error": str(e)}, status=500)

        if settings.BEPAID_SECRET_KEY == signature:
            notification = request.data
            try:
                if notification["state"] == "active":
                    if notification["additional_data"]["promo_code"]:
                        try:
                            promo_code_obj = PromoCode.objects.get(
                                name=notification["additional_data"]["promo_code"]
                            )
                            promo_code_obj.uses_count -= 1
                            promo_code_obj.save()
                        except PromoCode.DoesNotExist:
                            pass
                    school = get_object_or_404(
                        School, name=notification["additional_data"]["school"]
                    )
                    tariff = get_object_or_404(
                        Tariff, name=notification["additional_data"]["tariff"]
                    )
                    school.tariff = tariff

                    # Получаем количество дней подписки
                    subscription_days = notification["plan"]["plan"]["interval"]

                    # Вычисляем дату окончания подписки
                    if school.purchased_tariff_end_date:
                        expiration_date = (
                            school.purchased_tariff_end_date
                            + timezone.timedelta(days=subscription_days)
                        )
                    else:
                        expiration_date = timezone.now() + timezone.timedelta(
                            days=subscription_days
                        )
                    school.purchased_tariff_end_date = expiration_date
                    school.trial_end_date = None
                    school.save()

                    subscription, created = UserSubscription.objects.get_or_create(
                        user=school.owner,
                        school=school,
                        subscription_id=notification["id"],
                        expires_at=expiration_date,
                    )
                    # Если запись уже существует и была обновлена или создана новая запись
                    if not created:
                        # Обновляем поля subscription_id и expires_at
                        subscription.subscription_id = notification["id"]
                        subscription.expires_at = expiration_date
                        subscription.save()
                    return Response(status=status.HTTP_200_OK)

                if notification["state"] == "trial":
                    if notification["additional_data"]["trial_days"]:
                        subscription_days = notification["additional_data"][
                            "trial_days"
                        ]
                        school = get_object_or_404(
                            School, name=notification["additional_data"]["school"]
                        )
                        tariff = get_object_or_404(
                            Tariff, name=notification["additional_data"]["tariff"]
                        )
                        school.tariff = tariff
                        # Вычисляем дату окончания подписки
                        if school.purchased_tariff_end_date:
                            expiration_date = (
                                school.purchased_tariff_end_date
                                + timezone.timedelta(days=subscription_days)
                            )
                        else:
                            expiration_date = timezone.now() + timezone.timedelta(
                                days=subscription_days
                            )

                        school.purchased_tariff_end_date = expiration_date
                        school.trial_end_date = None
                        school.save()

                        return Response(status=status.HTTP_200_OK)
                if notification["state"] == "canceled":
                    school = get_object_or_404(
                        School, name=notification["additional_data"]["school"]
                    )
                    subscription = UserSubscription.objects.filter(
                        user=school.owner,
                        school=school,
                        subscription_id=notification["id"],
                    )
                    if subscription.exists():
                        subscription.delete()
                    return Response(status=status.HTTP_200_OK)
                else:
                    # Обработка случаев, когда состояние уведомления не "active" или "trial"
                    return Response(
                        {"error": "Статус оплаты не подтвержден."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        else:
            return Response(
                {"error": "Invalid Signature"},
                status=status.HTTP_400_BAD_REQUEST,
            )
