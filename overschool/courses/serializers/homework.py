from common_services.selectel_client import UploadToS3
from common_services.serializers import AudioFileGetSerializer, TextFileGetSerializer
from courses.models import BaseLesson, BaseLessonBlock, Homework
from courses.models.homework.user_homework import UserHomework
from courses.models.homework.user_homework_check import UserHomeworkCheck
from courses.serializers.block import BlockDetailSerializer
from courses.serializers.user_homework_check import UserHomeworkCheckDetailSerializer
from rest_framework import serializers

s3 = UploadToS3()


class HomeworkSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели домашнего задания
    """

    type = serializers.CharField(default="homework", read_only=True)

    class Meta:
        model = Homework
        fields = [
            "homework_id",
            "baselesson_ptr_id",
            "section",
            "name",
            "order",
            "author_id",
            "automate_accept",
            "time_accept",
            "points",
            "type",
            "active",
        ]

    def create(self, validated_data):
        homework = Homework.objects.create(**validated_data)
        return homework

    def update(self, instance, validated_data):
        instance.section = validated_data.get("section", instance.section)
        instance.name = validated_data.get("name", instance.name)
        instance.order = validated_data.get("order", instance.order)
        instance.points = validated_data.get("points", instance.points)
        instance.automate_accept = validated_data.get(
            "automate_accept", instance.automate_accept
        )
        instance.time_accept = validated_data.get("time_accept", instance.time_accept)
        instance.active = validated_data.get("active", instance.active)

        instance.save()

        return instance


class HomeworkDetailSerializer(serializers.ModelSerializer):
    blocks = serializers.SerializerMethodField()
    audio_files = AudioFileGetSerializer(many=True, required=False)
    text_files = TextFileGetSerializer(many=True, required=False)
    type = serializers.CharField(default="homework", read_only=True)
    user_mark = serializers.SerializerMethodField()
    user_homework_checks = serializers.SerializerMethodField()

    class Meta:
        model = Homework
        fields = [
            "homework_id",
            "baselesson_ptr_id",
            "section",
            "name",
            "order",
            "author_id",
            "automate_accept",
            "time_accept",
            "points",
            "text_files",
            "audio_files",
            "blocks",
            "type",
            "user_mark",
            "user_homework_checks",
            "active",
        ]
        read_only_fields = [
            "type",
            "text_files",
            "audio_files",
            "blocks",
            "user_homework_checks",
            "user_mark",
        ]

    def get_blocks(self, obj):
        return BlockDetailSerializer(obj.blocks.order_by("order"), many=True).data

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
