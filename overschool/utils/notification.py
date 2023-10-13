import hashlib
import hmac

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class PaymentNotificationSerializer(serializers.Serializer):
    pass


class PaymentNotificationView(LoggingMixin, WithHeadersViewSet, APIView):
    permission_classes = [AllowAny]
    serializer_class = PaymentNotificationSerializer

    def post(self, request):
        signature = request.META["HTTP_AUTHORIZATION"]
        SECRET_KEY = "0537f88488ebd20593e0d0f28841630420820aeef1a21f592c9ce413525d9d02"
        body_bytes = bytes(request.body)
        digest = (
            hmac.new(SECRET_KEY.encode(), msg=body_bytes, digestmod=hashlib.sha256)
            .hexdigest()
            .lower()
        )
        if digest == signature:
            notification = request.data

            return Response({"received": notification["additional_data"]})
        else:
            notification = request.data
            n = notification["additional_data"]
            a = n["tariff"]
            return Response(
                {
                    "error": f"Invalid Signature {digest}!={signature}!={request.META}!={a}, {n}, {a}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
