from common_services.selectel_client import SelectelClient
from common_services.serializers import AudioFileGetSerializer, TextFileGetSerializer
from courses.models import BaseLesson, Lesson, LessonComponentsOrder
from rest_framework import serializers

from .lesson_components_order import LessonComponentsOrderSerializer

s = SelectelClient()


class LessonSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели урока
    """

    type = serializers.CharField(default="lesson", read_only=True)
    all_components = LessonComponentsOrderSerializer(many=True, required=False)

    class Meta:
        model = Lesson
        fields = [
            "lesson_id",
            "baselesson_ptr_id",
            "section",
            "name",
            "order",
            "author_id",
            "description",
            "video",
            "points",
            "type",
            "all_components",
        ]

    def create(self, validated_data):
        components_data = validated_data.pop("all_components", None)
        lesson = Lesson.objects.create(**validated_data)
        if components_data:
            base_lesson = BaseLesson.objects.get(lessons=lesson)
            for component_data in components_data:
                LessonComponentsOrder.objects.create(
                    base_lesson=base_lesson, **component_data
                )
        return lesson

    def update(self, instance, validated_data):
        if "all_components" in validated_data:
            components_data = validated_data.pop("all_components")
            base_lesson = BaseLesson.objects.get(lessons=instance)

            for component_data in components_data:
                LessonComponentsOrder.objects.update_or_create(
                    base_lesson=base_lesson,
                    order=component_data.get("order"),
                    defaults={"component_type": component_data.get("component_type")},
                )

        instance.section = validated_data.get("section", instance.section)
        instance.name = validated_data.get("name", instance.name)
        instance.order = validated_data.get("order", instance.order)
        instance.description = validated_data.get("description", instance.description)
        instance.video = validated_data.get("video", instance.video)
        instance.points = validated_data.get("points", instance.points)

        instance.save()

        return instance


class LessonDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор для просмотра конкретного урока
    """

    video = serializers.SerializerMethodField()
    audio_files = AudioFileGetSerializer(many=True, required=False)
    text_files = TextFileGetSerializer(many=True, required=False)
    type = serializers.CharField(default="lesson", read_only=True)
    all_components = LessonComponentsOrderSerializer(many=True, required=False)

    class Meta:
        model = Lesson
        fields = [
            "lesson_id",
            "baselesson_ptr_id",
            "section",
            "name",
            "order",
            "author_id",
            "description",
            "video",
            "points",
            "text_files",
            "audio_files",
            "type",
            "all_components",
        ]
        read_only_fields = ["type", "text_files", "audio_files"]

    def get_video(self, obj):
        return s.get_selectel_link(str(obj.video)) if obj.video else None
