from rest_framework import serializers
from schools.models import School, SchoolBranding


class BrandingSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели ребрендинга
    """

    class Meta:
        model = SchoolBranding
        fields = "__all__"


class SchoolBrandingSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели школы с полями ребрендинга
    """

    branding = BrandingSerializer()

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
            "branding",
        ]
