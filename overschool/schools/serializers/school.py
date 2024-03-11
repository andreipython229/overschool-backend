import requests
from rest_framework import serializers
from schools.models import School, Tariff, TariffPlan
from transliterate import translit


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
            "contact_link",
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

        attrs["name"] = translit(attrs.get("name"), "ru", reversed=True)
        attrs["name"] = attrs["name"].replace(" ", "_")
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
            "contact_link",
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
            attrs["name"] = translit(attrs.get("name"), "ru", reversed=True)
            attrs["name"] = attrs["name"].replace(" ", "_")
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
            "contact_link",
        ]


class TariffSerializer(serializers.ModelSerializer):
    price_rf_rub = serializers.SerializerMethodField()

    class Meta:
        model = Tariff
        fields = [
            "id",
            "name",
            "price",
            "number_of_courses",
            "number_of_staff",
            "students_per_month",
            "total_students",
            "price_rf_rub",
        ]

    def get_price_rf_rub(self, obj):
        if float(obj.price) == 0.00:
            return 0.00

        # Получение курса российского рубля от НБРБ
        url = "https://api.nbrb.by/exrates/rates/456"

        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            rate = data.get("Cur_OfficialRate", 1)
            return round((float(obj.price) / rate) * 100)
        else:
            return None
