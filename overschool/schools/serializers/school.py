import re

from rest_framework import serializers
from schools.models import School, Tariff, TariffPlan


class SelectTrialSerializer(serializers.ModelSerializer):
    """
    Сериализатор для выбора пробного тарифа школы
    """

    tariff = serializers.ChoiceField(choices=TariffPlan.choices)

    class Meta:
        model = School
        fields = ["tariff"]


class SchoolSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели школы
    """

    class Meta:
        model = School
        fields = [
            "school_id",
            "name",
            "order",
            "tariff",
            "purchased_tariff_end_date",
            "used_trial",
            "trial_end_date",
            "created_at",
            "updated_at",
            "offer_url",
        ]
        read_only_fields = [
            "order",
            "tariff",
            "purchased_tariff_end_date",
            "used_trial",
            "trial_end_date",
        ]

    def validate(self, attrs):
        if not attrs.get("name"):
            raise serializers.ValidationError("'name' обязателеное поле.")

        attrs["name"] = re.sub(r"[^A-Za-z0-9._-]", "", attrs.get("name"))

        return attrs


class SchoolUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления модели школы
    """

    class Meta:
        model = School
        fields = [
            "school_id",
            "name",
            "order",
            "tariff",
            "purchased_tariff_end_date",
            "used_trial",
            "trial_end_date",
            "created_at",
            "updated_at",
            "offer_url",
        ]
        read_only_fields = [
            "order",
            "tariff",
            "purchased_tariff_end_date",
            "used_trial",
            "trial_end_date",
        ]

    def validate(self, attrs):
        if attrs.get("name"):
            attrs["name"] = re.sub(r"[^A-Za-z0-9._-]", "", attrs.get("name"))
        return attrs


class SchoolGetSerializer(serializers.ModelSerializer):
    """
    Сериализатор просмотра школы
    """

    class Meta:
        model = School
        fields = [
            "school_id",
            "name",
            "order",
            "tariff",
            "purchased_tariff_end_date",
            "used_trial",
            "trial_end_date",
            "created_at",
            "updated_at",
            "owner",
            "offer_url",
        ]


class TariffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tariff
        fields = "__all__"
