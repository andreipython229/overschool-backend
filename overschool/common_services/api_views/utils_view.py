from common_services.bepaid_client import BePaidClient
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.serializers import SubscriptionSerializer
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import permissions, serializers, status
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
        school_obj = get_object_or_404(School, name=school)
        if user != school_obj.owner:
            return Response(
                {"error": "Пользователь не является владельцем школы"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Проверяем, есть ли у пользователя активная подписка
        user_subscription = UserSubscription.objects.filter(
            user=user, school=school_obj
        ).first()

        # Создаем подписку
        bepaid_client = BePaidClient(
            shop_id=settings.BEPAID_SHOP_ID,
            secret_key=settings.BEPAID_SECRET_KEY,
            is_test=True,
        )

        # Если есть активная подписка, проверяем ее статус
        if user_subscription:
            subscription_status = bepaid_client.get_subscription_status(
                user_subscription.subscription_id
            )
            if subscription_status["state"] not in ["active", "trial"]:
                # Если подписка не активна, удаляем ее
                user_subscription.delete()

        serializer = SubscriptionSerializer(
            data=request.data,
            context={"school": school_obj, "user_subscription": user_subscription},
        )
        if serializer.is_valid():
            data = serializer.validated_data
            tariff = data["tariff"]
            pays_count = data.get(
                "pays_count"
            )  # Может быть None для ежемесячной оплаты
            promo_code = request.data.get("promo_code")
            subscription_type = data.get("subscription_type")
            trial_days = data.get("trial_days")

            # Получаем объект тарифа
            tariff_obj = Tariff.objects.get(name=tariff)

            # Вычисляем сумму с учетом скидки за предоплату, если указано pays_count
            if pays_count is not None:
                if pays_count in [3, 6, 12]:
                    if pays_count == 3:
                        to_pay_sum = tariff_obj.discount_3_months
                    elif pays_count == 6:
                        to_pay_sum = tariff_obj.discount_6_months
                    elif pays_count == 12:
                        to_pay_sum = tariff_obj.discount_12_months
                else:
                    return Response(
                        {"error": "Недопустимое значение pays_count"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                # Иначе используем базовую цену без скидки
                to_pay_sum = tariff_obj.price

            # Применяем скидку промокода, если он указан

            if promo_code:
                try:
                    promo_code_obj = PromoCode.objects.get(
                        name=promo_code, uses_count__gt=0
                    )
                    to_pay_sum = float(to_pay_sum) * (1 - promo_code_obj.discount / 100)
                except PromoCode.DoesNotExist:
                    return Response(
                        {"error": "Промокод не найден"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            if subscription_type == "upfront":
                # Вычисляем количество дней, на которые пользователь оплатил подписку
                subscription_days = 30 * pays_count

                # Создаем подписку с указанным количеством дней
                subscribe_res = bepaid_client.subscribe_client(
                    request=request,
                    to_pay_sum=to_pay_sum * 100,
                    days_interval=subscription_days,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    email=user.email,
                    phone=str(user.phone_number),
                    tariff=tariff,
                    school=school,
                    promo_code=promo_code,
                    trial_days=trial_days,
                )
            else:  # Подписка ежемесячная
                subscribe_res = bepaid_client.subscribe_client(
                    request=request,
                    to_pay_sum=to_pay_sum * 100,
                    days_interval=serializer.fields["days_interval"].default,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    email=user.email,
                    phone=str(user.phone_number),
                    tariff=tariff,
                    school=school,
                    promo_code=promo_code,
                    trial_days=trial_days,
                )

            return Response(subscribe_res, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UnsubscribeClientSerializer(serializers.Serializer):
    pass


class UnsubscribeClientView(LoggingMixin, WithHeadersViewSet, SchoolMixin, APIView):
    serializer_class = UnsubscribeClientSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        school = kwargs.get("school_name")
        if not user:
            return Response(
                {"error": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND
            )
        school_obj = School.objects.get(name=school)
        if not (user == school_obj.owner or user.is_staff and user.is_superuser):
            return Response(
                {
                    "error": "Пользователь не является владельцем школы или администратором"
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        bepaid_client = BePaidClient(
            shop_id=settings.BEPAID_SHOP_ID,
            secret_key=settings.BEPAID_SECRET_KEY,
            is_test=True,
        )

        user_subscription = UserSubscription.objects.filter(
            user=school_obj.owner, school=school_obj
        ).first()

        if not user_subscription:
            return Response(
                {"error": "Пользователь не имеет подписки"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subscription_id = user_subscription.subscription_id
        response = bepaid_client.unsubscribe(subscription_id)
        if response.status_code != 200:
            return Response(
                {"error": "Не удалось отписаться от подписки"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_subscription.delete()

        return Response({"message": "Подписка отменена"}, status=status.HTTP_200_OK)
