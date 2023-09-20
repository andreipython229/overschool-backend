from courses.models import Section, Lesson, SectionTest, Homework
from courses.serializers import LessonSerializer, HomeworkSerializer
from rest_framework import serializers


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
        fields = ["order", "section_id", "course", "name", "lessons"]
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
