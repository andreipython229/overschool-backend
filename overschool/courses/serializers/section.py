from courses.models import (
    Homework,
    Lesson,
    Section,
    SectionTest,
    StudentsGroup,
    StudentsGroupSettings,
)
from courses.serializers.homework import HomeworkSerializer
from courses.serializers.lesson import LessonSerializer
from rest_framework import serializers

from .students_group_settings import StudentsGroupSettingsSerializer


class TestSectionSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели теста
    """

    type = serializers.CharField(default="test", read_only=True)

    class Meta:
        model = SectionTest
        fields = [
            "test_id",
            "baselesson_ptr_id",
            "random_test_generator",
            "num_questions",
            "section",
            "name",
            "success_percent",
            "random_questions",
            "random_answers",
            "show_right_answers",
            "attempt_limit",
            "attempt_count",
            "points_per_answer",
            "points",
            "points",
            "has_timer",
            "order",
            "author_id",
            "type",
            "active",
        ]
        read_only_fields = ["type", "order"]


class SectionSerializer(serializers.ModelSerializer):
    lessons = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = ["order", "section_id", "course", "name", "lessons", "order"]

    def get_lessons(self, instance):
        lessons_data = instance.lessons.all()
        serialized_lessons = []

        sorted_lessons = sorted(lessons_data, key=lambda x: x.order)

        for lesson_data in sorted_lessons:
            try:
                homework_data = Homework.objects.get(baselesson_ptr=lesson_data.id)
                serializer = HomeworkSerializer(homework_data)
            except Homework.DoesNotExist:
                pass
            try:
                lesson_data = Lesson.objects.get(baselesson_ptr=lesson_data.id)
                serializer = LessonSerializer(lesson_data)
            except Lesson.DoesNotExist:
                pass
            try:
                test_data = SectionTest.objects.get(baselesson_ptr=lesson_data.id)
                serializer = TestSectionSerializer(test_data)
            except SectionTest.DoesNotExist:
                pass

            serialized_lessons.append(serializer.data)

        return serialized_lessons


class SectionRetrieveSerializer(serializers.ModelSerializer):
    lessons = serializers.SerializerMethodField()
    group_settings = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = ["order", "section_id", "course", "name", "group_settings", "lessons"]
        read_only_fields = ["order"]

    def get_lessons(self, instance):
        lessons_data = instance.lessons.all()
        serialized_lessons = []

        for lesson_data in lessons_data:
            try:
                homework_data = Homework.objects.get(baselesson_ptr=lesson_data.id)
                serializer = HomeworkSerializer(homework_data)
            except Homework.DoesNotExist:
                pass
            try:
                lesson_data = Lesson.objects.get(baselesson_ptr=lesson_data.id)
                serializer = LessonSerializer(lesson_data)
            except Lesson.DoesNotExist:
                pass
            try:
                test_data = SectionTest.objects.get(baselesson_ptr=lesson_data.id)
                serializer = TestSectionSerializer(test_data)
            except SectionTest.DoesNotExist:
                pass

            serialized_lessons.append(serializer.data)

        return serialized_lessons

    def get_group_settings(self, obj):
        user = self.context["request"].user
        if user.groups.filter(
                group__name="Student", school=obj.course.school_id
        ).exists():
            try:
                group = StudentsGroup.objects.get(
                    course_id=obj.course_id, students=user.pk
                )
                group_settings = StudentsGroupSettings.objects.get(
                    pk=group.group_settings_id
                )
                group_settings_data = StudentsGroupSettingsSerializer(
                    group_settings
                ).data
                return group_settings_data
            except StudentsGroup.DoesNotExist:
                return None
            except StudentsGroupSettings.DoesNotExist:
                return None
        return None


class SectionOrderSerializer(serializers.Serializer):
    section_id = serializers.IntegerField()
    order = serializers.IntegerField()
