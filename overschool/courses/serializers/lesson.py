from common_services.selectel_client import UploadToS3
from common_services.serializers import AudioFileGetSerializer, TextFileGetSerializer
from courses.models import (
    BaseLesson,
    BaseLessonBlock,
    Lesson,
    LessonAvailability,
    LessonEnrollment,
)
from rest_framework import serializers

s3 = UploadToS3()


class BaseLessonBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseLessonBlock
        fields = "__all__"


class LessonSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели урока
    """

    type = serializers.CharField(default="lesson", read_only=True)
    video_use = serializers.BooleanField(required=False)
    blocks = serializers.SerializerMethodField()

    def get_blocks(self, obj):
        blocks = BaseLessonBlock.objects.filter(lesson=obj)
        serializer = BaseLessonBlockSerializer(blocks, many=True)
        return serializer.data

    class Meta:
        model = Lesson
        fields = [
            "lesson_id",
            "baselesson_ptr_id",
            "section",
            "name",
            "order",
            "author_id",
            "blocks",
            "video_use",
            "points",
            "type",
            "active",
        ]
        read_only_fields = ["order, blocks"]

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

    # video = serializers.SerializerMethodField()
    audio_files = AudioFileGetSerializer(many=True, required=False)
    text_files = TextFileGetSerializer(many=True, required=False)
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
            "text_files",
            "audio_files",
            "type",
            "active",
            "url",
        ]
        read_only_fields = ["type", "text_files", "audio_files"]

    # def get_video(self, obj):
    #     return s3.get_link(obj.video.name) if obj.video else None


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
