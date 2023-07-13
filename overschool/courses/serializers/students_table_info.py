from rest_framework import serializers

from courses.models import StudentsTableInfo


class StudentsTableInfoSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели отображения информации о студентах в таблице у админа
    """

    class Meta:
        model = StudentsTableInfo
        fields = "__all__"


class StudentsTableInfoDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentsTableInfo
        fields = "__all__"
        read_only_fields = ['author', 'school', 'type']

    def validate_students_table_info(self, value):
        if not value:
            return self.instance.students_table_info
        for item in value:
            if item["id"] > 2:
                self.instance.students_table_info[item["id"] - 1]["order"] = item["order"]
                self.instance.students_table_info[item["id"] - 1]["checked"] = item["checked"]
            else:
                item["order"] = self.instance.students_table_info[item["id"] - 1]["order"]
                item["checked"] = self.instance.students_table_info[item["id"] - 1]["checked"]
        return value

    def update(self, instance, validated_data):
        students_table_info = validated_data.get("students_table_info")
        if students_table_info is not None:
            validated_data["students_table_info"] = self.validate_students_table_info(students_table_info)
        return super().update(instance, validated_data)
