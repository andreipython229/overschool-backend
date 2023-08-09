from common_services.selectel_client import SelectelClient
from common_services.serializers import AudioFileGetSerializer, TextFileGetSerializer
from courses.models import BaseLesson, Homework, LessonComponentsOrder
from courses.models.homework.user_homework import UserHomework
from courses.models.homework.user_homework_check import UserHomeworkCheck
from courses.serializers.user_homework_check import UserHomeworkCheckDetailSerializer
from rest_framework import serializers

from .lesson_components_order import LessonComponentsOrderSerializer

s = SelectelClient()


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
            "baselesson_ptr_id",
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
            "active",
        ]

    def create(self, validated_data):
        components_data = validated_data.pop("all_components", None)
        homework = Homework.objects.create(**validated_data)
        if components_data:
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
        instance.active = validated_data.get("active", instance.active)

        instance.save()

        return instance


class HomeworkDetailSerializer(serializers.ModelSerializer):
    video = serializers.SerializerMethodField()
    audio_files = AudioFileGetSerializer(many=True, required=False)
    text_files = TextFileGetSerializer(many=True, required=False)
    type = serializers.CharField(default="homework", read_only=True)
    user_mark = serializers.SerializerMethodField()
    user_homework_checks = serializers.SerializerMethodField()
    all_components = LessonComponentsOrderSerializer(many=True, required=False)

    class Meta:
        model = Homework
        fields = [
            "homework_id",
            "baselesson_ptr_id",
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
            "user_mark",
            "user_homework_checks",
            "all_components",
            "active",
        ]
        read_only_fields = [
            "type",
            "text_files",
            "audio_files",
            "user_homework_checks",
            "user_mark",
        ]

    def get_video(self, obj):
        return s.get_selectel_link(str(obj.video)) if obj.video else None

    def get_user_homework_checks(self, obj):
        user = self.context["request"].user
        user_homework_checks = UserHomeworkCheck.objects.filter(
            user_homework__homework=obj, user_homework__user=user
        ).order_by("-created_at")
        if user_homework_checks:
            serializer = UserHomeworkCheckDetailSerializer(
                user_homework_checks, many=True
            )
            return serializer.data
        return None

    def get_user_mark(self, obj):
        user = self.context["request"].user
        user_mark_exists = UserHomework.objects.filter(homework=obj, user=user).exists()
        if user_mark_exists:
            return UserHomework.objects.get(homework=obj, user=user).mark
        return None
