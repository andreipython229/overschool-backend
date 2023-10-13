import base64

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
        auth_type, auth_b64_string = signature.split(" ")
        auth_bytes = base64.b64decode(auth_b64_string)
        auth_string = auth_bytes.decode("utf-8")
        SECRET_KEY = "0537f88488ebd20593e0d0f28841630420820aeef1a21f592c9ce413525d9d02"

        if SECRET_KEY == auth_string:
            notification = request.data

            return Response(status=status.HTTP_200_OK)
        else:
            notification = request.data
            n = notification["additional_data"]
            n["tariff"]
            return Response(
                {
                    "error": f"Invalid Signature {SECRET_KEY}!={auth_string}!={auth_bytes}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
