from common_services.selectel_client import UploadToS3
from courses.models import StudentsGroup
from rest_framework import serializers
from schools.models import Bonus

s3 = UploadToS3()


class BonusSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели бонусов школы
    """

    student_groups = serializers.PrimaryKeyRelatedField(
        queryset=StudentsGroup.objects.all(), many=True, required=False
    )

    class Meta:
        model = Bonus
        fields = [
            "id",
            "logo",
            "text",
            "link",
            "expire_date",
            "active",
            "student_groups",
        ]

    def validate(self, attrs):
        instance = getattr(self, "instance", None)
        view = self.context.get("view")
        active = attrs.get("active")

        if view.request.method in ["PUT", "PATCH", "POST"]:
            if active:
                active_bonuses = Bonus.objects.filter(
                    school=view.get_school(), active=True
                )
                if instance:
                    active_bonuses = active_bonuses.exclude(pk=instance.pk)
                if active_bonuses.exists():
                    raise serializers.ValidationError(
                        "В школе уже есть действующая акция."
                    )

        return attrs


class BonusGetSerializer(serializers.ModelSerializer):
    """
    Сериализатор просмотра бонусов школы
    """

    logo = serializers.SerializerMethodField()

    class Meta:
        model = Bonus
        fields = [
            "id",
            "logo",
            "text",
            "link",
            "expire_date",
            "active",
            "student_groups",
        ]

    def get_logo(self, obj):
        return s3.get_link(obj.logo.name) if obj.logo else None
