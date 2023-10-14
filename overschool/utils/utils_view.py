from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from schools.models import PromoCode, Tariff
from utils.serializers import SubscriptionSerializer

from .bepaid_client import BePaidClient


class SubscribeClientView(WithHeadersViewSet, LoggingMixin, APIView):
    serializer_class = SubscriptionSerializer

    def post(self, request):
        user = request.user
        if not user:
            return Response(
                {"error": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND
            )

        # Проверяем, есть ли у пользователя активная подписка
        if user.subscription_id:
            return Response(
                {"error": "Пользователь уже имеет активную подписку"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SubscriptionSerializer(data=request.data, context={"user": user})
        if serializer.is_valid():
            data = serializer.validated_data
            tariff = data["tariff"]
            pays_count = data["pays_count"]
            promo_code = request.data.get("promo_code", " ")

            bepaid_client = BePaidClient(
                shop_id=settings.BEPAID_SHOP_ID,
                secret_key=settings.BEPAID_SECRET_KEY,
                is_test=True,
            )
            to_pay_sum = Tariff.objects.values_list("price", flat=True).get(name=tariff)
            if promo_code:
                try:
                    promo_code_obj = PromoCode.objects.get(
                        name=promo_code, uses_count__gt=0
                    )
                except PromoCode.DoesNotExist:
                    return Response(
                        {"error": "Промокод не найден"}, status=status.HTTP_404_NOT_FOUND
                    )
                to_pay_sum = float(to_pay_sum) * (1 - promo_code_obj.discount / 100)

            subscribe_res = bepaid_client.subscribe_client(
                request=request,
                to_pay_sum=to_pay_sum * 100,
                days_interval=serializer.fields["days_interval"].default,
                pays_count=pays_count,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                phone=str(user.phone_number),
                tariff=tariff,
                promo_code=promo_code,
            )
            user.subscription_id = subscribe_res.get("id")
            user.save(update_fields=["subscription_id"])

            return Response(subscribe_res, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UnsubscribeClientView(WithHeadersViewSet, LoggingMixin, APIView):
    serializer_class = SubscriptionSerializer

    def post(self, request):
        user = request.user
        if not user:
            return Response(
                {"error": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND
            )

        bepaid_client = BePaidClient(
            shop_id=settings.BEPAID_SHOP_ID,
            secret_key=settings.BEPAID_SECRET_KEY,
            is_test=True,
        )

        subscription_id = user.subscription_id

        if not subscription_id:
            return Response(
                {"error": "Пользователь не имеет подписки"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bepaid_client.unsubscribe(subscription_id)

        user.subscription_id = None
        user.save(update_fields=["subscription_id"])

        return Response({"message": "Подписка отменена"}, status=status.HTTP_200_OK)
