from common_services.selectel_client import SelectelClient
from rest_framework import serializers
from schools.models import School, TariffPlan, Tariff

s = SelectelClient()


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
            "avatar",
            "avatar_url",
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


class SchoolGetSerializer(serializers.ModelSerializer):
    """
    Сериализатор просмотра школы
    """

    avatar = serializers.SerializerMethodField()

    class Meta:
        model = School
        fields = [
            "school_id",
            "name",
            "avatar",
            "avatar_url",
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

    def get_avatar(self, obj):
        return s.get_selectel_link(str(obj.avatar)) if obj.avatar else None


class TariffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tariff
        fields = '__all__'
