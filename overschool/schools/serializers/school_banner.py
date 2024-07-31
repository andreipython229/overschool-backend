from rest_framework import serializers
from schools.models import Banner, BannerAccept, BannerClick


class BannerClickSerializer(serializers.ModelSerializer):
    class Meta:
        model = BannerClick
        fields = "__all__"


class BannerAcceptSerializer(serializers.ModelSerializer):
    class Meta:
        model = BannerAccept
        fields = "__all__"


class BannerSerializer(serializers.ModelSerializer):
    clicks_count = serializers.SerializerMethodField()
    unique_clicks_count = serializers.SerializerMethodField()
    is_accepted_by_user = serializers.SerializerMethodField()

    class Meta:
        model = Banner
        fields = "__all__"
        read_only_fields = ["school"]

    def get_clicks_count(self, obj):
        return obj.clicks.count()

    def get_unique_clicks_count(self, obj):
        return obj.clicks.values("user").distinct().count()

    def get_is_accepted_by_user(self, obj):
        user = self.context["request"].user
        print(user)
        return obj.accepts.filter(user=user, is_accepted=True).exists()
