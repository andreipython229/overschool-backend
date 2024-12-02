import requests
from common_services.selectel_client import UploadToS3
from rest_framework import serializers
from schools.models import (
    School,
    SchoolBranding,
    SchoolStudentsTableSettings,
    SchoolTask,
    Tariff,
    TariffPlan,
)
from transliterate import translit

s3 = UploadToS3()


class SchoolBrandingUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления модели ребрендинга.
    """

    platform_logo = serializers.SerializerMethodField()

    class Meta:
        model = SchoolBranding
        fields = [
            "platform_logo",
            "email",
            "phone",
            "unp",
            "full_organization_name",
            "address",
        ]

    def get_platform_logo(self, obj):
        if obj.platform_logo:
            return s3.get_link(obj.platform_logo.name)
        else:
            # Если нет загруженной картинки, вернуть ссылку на дефолтное изображение
            default_image_path = "base_school.jpg"
            return s3.get_link(default_image_path)


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
            "referral_code",
            "test_course",
            "rebranding_enabled",
            "telegram_link",
            "instagram_link",
            "twitter_link",
            "vk_link",
            "youtube_link",
            "extra_link",
        ]
        read_only_fields = [
            "order",
            "tariff",
            "purchased_tariff_end_date",
            "used_trial",
            "trial_end_date",
            "referral_code",
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

    branding = SchoolBrandingUpdateSerializer()

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
            "referral_code",
            "created_at",
            "updated_at",
            "offer_url",
            "contact_link",
            "test_course",
            "rebranding_enabled",
            "branding",
            "telegram_link",
            "instagram_link",
            "twitter_link",
            "vk_link",
            "youtube_link",
            "extra_link",
        ]
        read_only_fields = [
            "order",
            "tariff",
            "purchased_tariff_end_date",
            "used_trial",
            "trial_end_date",
            "referral_code",
        ]

    def validate(self, attrs):
        if attrs.get("name"):
            attrs["name"] = translit(attrs.get("name"), "ru", reversed=True)
            attrs["name"] = attrs["name"].replace(" ", "_")
        return attrs

    def update(self, instance, validated_data):
        # Обработка данных ребрендинга
        rebranding_data = validated_data.pop("branding", None)
        # Проверяем, включен ли ребрендинг
        if instance.rebranding_enabled:
            if rebranding_data:
                rebranding_instance = getattr(instance, "branding", None)
                if not rebranding_instance:
                    rebranding_instance = SchoolBranding.objects.create(school=instance)

                for attr, value in rebranding_data.items():
                    setattr(rebranding_instance, attr, value)
                rebranding_instance.save()
        else:
            # Если `rebranding_enabled` выключен, не обновляем и не создаем данные ребрендинга
            if rebranding_data:
                raise serializers.ValidationError(
                    "Нельзя обновить ребрендинг, так как он отключён."
                )
        # Обновляем остальные поля школы
        return super().update(instance, validated_data)


class SchoolGetSerializer(serializers.ModelSerializer):
    """
    Сериализатор просмотра школы
    """

    branding = SchoolBrandingUpdateSerializer()
    referral_count = serializers.SerializerMethodField()
    referral_click_count = serializers.SerializerMethodField()
    unique_referral_click_count = serializers.SerializerMethodField()

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
            "referral_code",
            "test_course",
            "referral_count",
            "referral_click_count",
            "unique_referral_click_count",
            "rebranding_enabled",
            "branding",
            "telegram_link",
            "instagram_link",
            "twitter_link",
            "vk_link",
            "youtube_link",
            "extra_link",
        ]
        read_only_fields = [
            "order",
            "tariff",
            "purchased_tariff_end_date",
            "used_trial",
            "trial_end_date",
            "referral_code",
        ]

    def get_referral_count(self, obj):
        return obj.referrals.count()

    def get_referral_click_count(self, obj):
        return obj.referral_clicks.count()

    def get_unique_referral_click_count(self, obj):
        return obj.referral_clicks.values("ip_address").distinct().count()

    def to_representation(self, instance):
        """
        Кастомизация представления данных: если ребрендинг отключен, поле rebranding не будет отображаться
        """
        representation = super().to_representation(instance)

        # Убираем поле rebranding, если ребрендинг отключен
        if not instance.rebranding_enabled:
            representation.pop("branding", None)

        return representation


class TariffSerializer(serializers.ModelSerializer):
    price_rf_rub = serializers.SerializerMethodField()
    discount_3_months_byn = serializers.SerializerMethodField()
    discount_3_months_rub = serializers.SerializerMethodField()
    discount_6_months_byn = serializers.SerializerMethodField()
    discount_6_months_rub = serializers.SerializerMethodField()
    discount_12_months_byn = serializers.SerializerMethodField()
    discount_12_months_rub = serializers.SerializerMethodField()

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
            "discount_3_months_byn",
            "discount_3_months_rub",
            "discount_6_months_byn",
            "discount_6_months_rub",
            "discount_12_months_byn",
            "discount_12_months_rub",
        ]

    def rf_rate(self):
        # Получение курса российского рубля от НБРБ
        url = "https://api.nbrb.by/exrates/rates/456"

        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            rate = data.get("Cur_OfficialRate", 1)
            return rate
        return None

    def get_price_rf_rub(self, obj):
        if float(obj.price) == 0.00:
            return 0.00

        rate = self.rf_rate()
        if rate is None:
            return None
        return round(
            (float(obj.price) / rate) * 100, 2
        )  # округление до двух знаков после запятой

    def get_discount_3_months_byn(self, obj):
        if obj.discount_3_months is not None:
            return obj.discount_3_months
        return None

    def get_discount_3_months_rub(self, obj):
        if obj.discount_3_months is not None:
            rate = self.rf_rate()
            if rate is None:
                return None
            return round((float(obj.discount_3_months) / rate) * 100, 2)
        return None

    def get_discount_6_months_byn(self, obj):
        if obj.discount_6_months is not None:
            return obj.discount_6_months
        return None

    def get_discount_6_months_rub(self, obj):
        if obj.discount_6_months is not None:
            rate = self.rf_rate()
            if rate is None:
                return None
            return round((float(obj.discount_6_months) / rate) * 100, 2)
        return None

    def get_discount_12_months_byn(self, obj):
        if obj.discount_12_months is not None:
            return obj.discount_12_months
        return None

    def get_discount_12_months_rub(self, obj):
        if obj.discount_12_months is not None:
            rate = self.rf_rate()
            if rate is None:
                return None
            return round((float(obj.discount_12_months) / rate) * 100, 2)
        return None


class SchoolStudentsTableSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolStudentsTableSettings
        fields = "__all__"


class SchoolTaskSummarySerializer(serializers.Serializer):
    total_tasks = serializers.IntegerField()
    total_completed_tasks = serializers.IntegerField()
    completion_percentage = serializers.FloatField()
    tasks = serializers.ListField(child=serializers.DictField())

    def to_representation(self, instance):
        return {
            "total_tasks": instance["total_tasks"],
            "total_completed_tasks": instance["total_completed_tasks"],
            "completion_percentage": instance["completion_percentage"],
            "tasks": instance["tasks"],
        }
