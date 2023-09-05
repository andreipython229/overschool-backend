from courses.models import LessonComponentsOrder
from rest_framework import serializers


class LessonComponentsOrderSerializer(serializers.ModelSerializer):
    """Сериализатор порядка компонентов внутри урока"""

    class Meta:
        model = LessonComponentsOrder
        fields = [
            "order",
            "component_type",
        ]
        read_only_fields = ["order"]
