from courses.models import UserTest
from rest_framework import serializers


class UserTestSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели выполненного теста
    """

    class Meta:
        model = UserTest
        fields = "__all__"

    def update(self, instance, validated_data):

        instance.status = validated_data.get("status", instance.status)
        instance.success_percent = validated_data.get(
            "success_percent", instance.success_percent
        )

        instance.save()

        return instance
