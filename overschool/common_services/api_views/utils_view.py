from common_services.bepaid_client import BePaidClient
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.serializers import SubscriptionSerializer
from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from schools.models import PromoCode, School, Tariff
from schools.school_mixin import SchoolMixin
from users.models import UserSubscription


class SubscribeClientView(LoggingMixin, WithHeadersViewSet, SchoolMixin, APIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        school = kwargs.get("school_name")
        if not user:
            return Response(
                {"error": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND
            )
        school_obj = School.objects.get(name=school)
        if user != school_obj.owner:
            return Response(
                {"error": "Пользователь не является владельцем школы"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Проверяем, есть ли у пользователя активная подписка
        user_subscription = UserSubscription.objects.filter(
            user=user, school=school_obj
        ).first()

        if user_subscription:
            return Response(
                {"error": "Пользователь уже имеет активную подписку для этой школы"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SubscriptionSerializer(data=request.data)
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
                        {"error": "Промокод не найден"},
                        status=status.HTTP_400_BAD_REQUEST,
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
                school=school,
                promo_code=promo_code,
            )

            return Response(subscribe_res, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UnsubscribeClientView(LoggingMixin, WithHeadersViewSet, SchoolMixin, APIView):
    def post(self, request, *args, **kwargs):
        user = request.user
        school = kwargs.get("school_name")
        if not user:
            return Response(
                {"error": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND
            )
        school_obj = School.objects.get(name=school)
        if user != school_obj.owner:
            return Response(
                {"error": "Пользователь не является владельцем школы"},
                status=status.HTTP_403_FORBIDDEN,
            )

        bepaid_client = BePaidClient(
            shop_id=settings.BEPAID_SHOP_ID,
            secret_key=settings.BEPAID_SECRET_KEY,
            is_test=True,
        )

        user_subscription = UserSubscription.objects.filter(
            user=user, school=school_obj
        ).first()

        if not user_subscription:
            return Response(
                {"error": "Пользователь не имеет подписки"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subscription_id = user_subscription.subscription_id
        bepaid_client.unsubscribe(subscription_id)

        user_subscription.delete()

        return Response({"message": "Подписка отменена"}, status=status.HTTP_200_OK)
