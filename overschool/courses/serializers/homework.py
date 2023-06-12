from common_services.serializers import AudioFileGetSerializer, TextFileGetSerializer
from courses.models import BaseLesson, Homework, LessonComponentsOrder
from rest_framework import serializers

from .lesson_components_order import LessonComponentsOrderSerializer


class HomeworkSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели домашнего задания
    """

    type = serializers.CharField(default="homework", read_only=True)
    all_components = LessonComponentsOrderSerializer(many=True, required=False)

    class Meta:
        model = Homework
        fields = [
            "homework_id",
            "section",
            "name",
            "order",
            "author_id",
            "description",
            "video",
            "automate_accept",
            "time_accept",
            "points",
            "type",
            "all_components",
        ]

    def create(self, validated_data):
        components_data = validated_data.pop("all_components")
        homework = Homework.objects.create(**validated_data)
        base_lesson = BaseLesson.objects.get(homeworks=homework)
        for component_data in components_data:
            LessonComponentsOrder.objects.create(
                base_lesson=base_lesson, **component_data
            )
        return homework

    def update(self, instance, validated_data):
        if "all_components" in validated_data:
            components_data = validated_data.pop("all_components")
            base_lesson = BaseLesson.objects.get(homeworks=instance)

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
        instance.automate_accept = validated_data.get(
            "automate_accept", instance.automate_accept
        )
        instance.time_accept = validated_data.get("time_accept", instance.time_accept)

        instance.save()

        return instance


class HomeworkDetailSerializer(serializers.ModelSerializer):
    audio_files = AudioFileGetSerializer(many=True, required=False)
    text_files = TextFileGetSerializer(many=True, required=False)
    type = serializers.CharField(default="homework", read_only=True)
    all_components = LessonComponentsOrderSerializer(many=True, required=False)

    class Meta:
        model = Homework
        fields = [
            "homework_id",
            "section",
            "name",
            "order",
            "author_id",
            "description",
            "video",
            "automate_accept",
            "time_accept",
            "points",
            "text_files",
            "audio_files",
            "type",
            "all_components",
        ]
        read_only_fields = ["type", "text_files", "audio_files"]


class HomeworkHistorySerializer(serializers.Serializer):
    class Meta:
        fields = [
            "homework_id",
            "section",
            "name",
            "order",
            "author_id",
            "description",
            "video",
            "automate_accept",
            "time_accept",
            "points",
            "user_homeworks__text",
            "audio_files",
            "type",
            "last_check_status",
            "last_check_response",
            "last_check_time",
            "last_check_teacher_avatar",
            "last_check_teacher_name",
            "last_check_teacher_lastname",
            "text_files",
        ]
