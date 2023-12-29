from courses.models import BaseLessonBlock
from rest_framework import serializers


class LessonBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseLessonBlock
        fields = [
            "base_lesson",
            "video",
            "url",
            "description",
            "code",
            "picture",
            "order",
        ]
        read_only_fields = ["order"]

    def validate(self, data):
        instance = getattr(self, "instance", None)
        base_lesson = data.get("base_lesson")
        video = data.get("video")
        url = data.get("url")
        description = data.get("description")
        code = data.get("code")
        picture = data.get("picture")

        fields_to_check = [video, url, description, code, picture]

        if not any(fields_to_check):
            raise serializers.ValidationError("Необходимо указать хотя бы одно поле")

        non_empty_fields = [field for field in fields_to_check if field is not None]
        if len(non_empty_fields) > 1:
            raise serializers.ValidationError("Можно указать только одно поле")

        if base_lesson and instance is None:
            existing_blocks_count = BaseLessonBlock.objects.filter(
                base_lesson=base_lesson
            ).count()
            if existing_blocks_count >= 10:
                raise serializers.ValidationError(
                    "Больше добавлять нельзя, уже 10 блоков"
                )

        return data
