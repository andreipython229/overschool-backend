import base64

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from schools.models import PromoCode, School, Tariff

User = get_user_model()


class PaymentNotificationSerializer(serializers.Serializer):
    pass


class PaymentNotificationView(LoggingMixin, WithHeadersViewSet, APIView):
    permission_classes = [AllowAny]
    serializer_class = PaymentNotificationSerializer

    def post(self, request):
        auth_header = request.META["HTTP_AUTHORIZATION"]
        auth_type, auth_b64_string = auth_header.split(" ")
        auth_bytes = base64.b64decode(auth_b64_string)
        auth_string = auth_bytes.decode("utf-8")
        signature = auth_string.split(":")[1]

        if settings.BEPAID_SECRET_KEY == signature:
            notification = request.data
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
                user = User.objects.get(subscription_id=notification["id"])
                school = School.objects.get(owner=user)
                tariff = Tariff.objects.get(
                    name=notification["additional_data"]["tariff"]
                )
                school.tariff = tariff
                school.purchased_tariff_end_date = timezone.now() + timezone.timedelta(
                    days=30
                )
                school.save()
            else:
                user = User.objects.get(subscription_id=notification["id"])
                user.subscription_id = None
                user.save()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Invalid Signature"},
                status=status.HTTP_400_BAD_REQUEST,
            )
