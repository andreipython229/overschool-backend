from common_services.selectel_client import UploadToS3
from rest_framework import serializers
from schools.models import Box, BoxPrize, Payment, Prize

s3 = UploadToS3()


class BoxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Box
        fields = [
            "name",
            "icon",
            "school",
            "price",
            "quantity",
            "bonus_quantity",
            "is_active",
            "auto_deactivation_time",
        ]
        read_only_fields = [
            "school",
        ]


class PrizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prize
        fields = [
            "name",
            "icon",
            "school",
            "drop_chance",
            "guaranteed_box_count",
            "is_active",
        ]
        read_only_fields = [
            "school",
        ]


class PrizeDetailSerializer(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()

    class Meta:
        model = Prize
        fields = [
            "id",
            "name",
            "icon",
            "school",
            "drop_chance",
            "guaranteed_box_count",
            "is_active",
        ]
        read_only_fields = [
            "school",
        ]

    def get_icon(self, obj):
        if obj.icon:
            return s3.get_link(obj.icon.name)
        else:
            return None


class BoxPrizeSerializer(serializers.ModelSerializer):
    """
    Сериалайзер для модели BoxPrize с вложенными данными о призах
    """

    prize = PrizeDetailSerializer()

    class Meta:
        model = BoxPrize
        fields = [
            "prize",
        ]


class BoxDetailSerializer(serializers.ModelSerializer):
    """
    Расширенный сериалайзер для модели Box с вложенными связями
    """

    icon = serializers.SerializerMethodField()
    prizes = BoxPrizeSerializer(many=True)

    class Meta:
        model = Box
        fields = [
            "id",
            "name",
            "icon",
            "school",
            "price",
            "quantity",
            "bonus_quantity",
            "is_active",
            "auto_deactivation_time",
            "prizes",
        ]
        read_only_fields = [
            "school",
        ]

    def get_icon(self, obj):
        if obj.icon:
            return s3.get_link(obj.icon.name)
        else:
            return None


class PaymentSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source="user.email")

    class Meta:
        model = Payment
        fields = [
            "id",
            "user",
            "email",
            "box",
            "amount",
            "school",
            "invoice_no",
            "payment_status",
        ]
