from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from utils.serializers import SubscriptionSerializer
from schools.models import Tariff
from .bepaid_client import BePaidClient


@swagger_auto_schema(method="post", request_body=SubscriptionSerializer)
@api_view(["POST"])
def subscribe_client(request,):
    user = request.user
    if not user:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    # Здесь передаем пользователя и данные из запроса в сериализатор
    serializer = SubscriptionSerializer(data=request.data, context={"user": user})
    if serializer.is_valid():
        data = serializer.validated_data
        tariff = data["tariff"]
        pays_count = data["pays_count"]


        bepaid_client = BePaidClient(
            shop_id="21930",
            secret_key="0537f88488ebd20593e0d0f28841630420820aeef1a21f592c9ce413525d9d02",
            is_test=True,
        )

        # логика для работы с тарифами, смены тарифов и т.д.
        subscribe_res = bepaid_client.subscribe_client(
            to_pay_sum=Tariff.objects.values_list('price', flat=True).get(name=tariff),
            days_interval=serializer.fields["days_interval"].default,
            pays_count=pays_count,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=str(user.phone_number),
        )

        return Response(subscribe_res, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(["POST"])
def unsubscribe_client(request, user_id):
    # логика для отписки от тарифа
    pass


@api_view(["POST"])
def recalculate_cost(request, user_id):
    # логика для перерасчета стоимости при смене тарифа
    pass


@api_view(["GET"])
def get_next_payment_time(request, user_id):
    # логика для получения информации о времени до следующего платежа
    pass
