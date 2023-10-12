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
        signature = request.headers.get("Content-Signature")
        shop_public_key = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAybT85/HNo9IXHRBoA32wgrnvUZaWK2RcNXoKZju2hRM+3B9KR5qD1aDXnKN2VzLe47XLhKaiiwbAAToThBAxVHhKh25PlerP9iAKLYDypihrbuJEq1QHQzPFRjIliE66NXKh6KGB0wv3ZCakaqAJgx3GH9fZKU5QdmSlYIwyfOI+z01T4cLmdDPOz/NAsgFBU0RwvPJd9aXXb7O8fm8MIxahksvU337BUSZjBbGUKWNIJ+6t4dLXQqv4o9axejRMkGmSY3Puq06t4nBqCgXdgwM3ovk5L6KjxaIw/Vc0edbf6bcLpj/GpML0k49GAisnn4jJaTiW2LzI2up8pj5uQwIDAQAB"
        body_bytes = bytes(request.body)
        digest = (
            hmac.new(shop_public_key.encode(), msg=body_bytes, digestmod=hashlib.sha256)
            .hexdigest()
            .lower()
        )
        if digest == signature:
            notification = request.data
            print(notification)

            return Response({"received": notification["additional_data"]})
        else:
            notification = request.data
            n = notification["additional_data"]
            a = n["tariff"]
            print("ошибка", notification)
            print(signature)
            print(digest)
            return Response(
                {"error": f"Invalid Signature {digest}!={signature}, {n}, {a}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
