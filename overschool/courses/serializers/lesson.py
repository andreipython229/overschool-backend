from common_services.selectel_client import UploadToS3
from common_services.serializers import AudioFileGetSerializer, TextFileGetSerializer
from courses.models import (
    BaseLesson,
    BaseLessonBlock,
    Lesson,
    LessonAvailability,
    LessonEnrollment,
)
from courses.serializers.block import BlockDetailSerializer
from rest_framework import serializers

s3 = UploadToS3()


class LessonSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели урока
    """

    type = serializers.CharField(default="lesson", read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "lesson_id",
            "baselesson_ptr_id",
            "section",
            "name",
            "order",
            "author_id",
            "points",
            "type",
            "active",
        ]
        read_only_fields = ["order"]

    def create(self, validated_data):
        lesson = Lesson.objects.create(**validated_data)
        return lesson

    def update(self, instance, validated_data):
        instance.section = validated_data.get("section", instance.section)
        instance.name = validated_data.get("name", instance.name)
        instance.order = validated_data.get("order", instance.order)
        instance.points = validated_data.get("points", instance.points)
        instance.active = validated_data.get("active", instance.active)

        instance.save()

        return instance


class LessonDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор для просмотра конкретного урока
    """

    audio_files = AudioFileGetSerializer(many=True, required=False)
    text_files = TextFileGetSerializer(many=True, required=False)
    type = serializers.CharField(default="lesson", read_only=True)
    blocks = BlockDetailSerializer(many=True, required=False)

    class Meta:
        model = Lesson
        fields = [
            "lesson_id",
            "baselesson_ptr_id",
            "section",
            "name",
            "order",
            "author_id",
            "points",
            "text_files",
            "audio_files",
            "type",
            "active",
            "blocks",
        ]
        read_only_fields = ["type", "text_files", "audio_files", "blocks"]


class LessonUpdateSerializer(serializers.Serializer):
    baselesson_ptr_id = serializers.IntegerField()
    order = serializers.IntegerField()


class LessonAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonAvailability
        fields = "__all__"


class LessonEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonEnrollment
        fields = "__all__"
