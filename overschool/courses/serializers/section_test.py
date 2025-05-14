from courses.models import RandomTestTests, SectionTest
from rest_framework import serializers


class RandomTestTestsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RandomTestTests
        fields = "__all__"


class TestSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели теста
    """

    type = serializers.CharField(default="test", read_only=True)

    tests_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = SectionTest
        fields = [
            "test_id",
            "baselesson_ptr_id",
            "random_test_generator",
            "num_questions",
            "tests_ids",
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
            "has_timer",
            "time_limit",
            "order",
            "author_id",
            "type",
            "active",
        ]
        read_only_fields = ["type"]

    def get_tests_ids(self, obj):
        test = SectionTest.objects.get(baselesson_ptr_id=obj.id)
        random_tests = RandomTestTests.objects.filter(test=test)
        return [random_test.target_test_id for random_test in random_tests]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if request and request.method == "GET":
            data["tests_ids"] = self.get_tests_ids(instance)
        return data

    def create(self, validated_data):
        tests_ids = validated_data.pop("tests_ids", [])

        # Проверка всех tests_ids на существование SectionTest объекта
        section_tests = SectionTest.objects.filter(pk__in=tests_ids)
        missing_ids = set(tests_ids) - set(section_tests.values_list("pk", flat=True))
        if missing_ids:
            raise serializers.ValidationError(
                f"SectionTest с идентификаторами {missing_ids} не найдены."
            )

        section_test = super().create(validated_data)

        for test_id in tests_ids:
            target = SectionTest.objects.get(pk=test_id)
            RandomTestTests.objects.create(test=section_test, target_test=target)

        return section_test

    def update(self, instance, validated_data):
        tests_ids = validated_data.pop("tests_ids", None)
        instance = super().update(instance, validated_data)
        if tests_ids is not None:
            RandomTestTests.objects.filter(test=instance).delete()
            for test_id in tests_ids:
                target = SectionTest.objects.get(pk=test_id)
                RandomTestTests.objects.create(test=instance, target_test=target)
        return instance

    def destroy(self, instance):
        RandomTestTests.objects.filter(test=instance).delete()
        instance.delete()
