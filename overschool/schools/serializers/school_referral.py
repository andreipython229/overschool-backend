from rest_framework import serializers
from schools.models import Referral, ReferralClick


class ReferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = Referral
        fields = "__all__"


class ReferralClickSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralClick
        fields = "__all__"
