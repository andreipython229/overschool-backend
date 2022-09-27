from datetime import date

from homeworks.models import UserHomework
from rest_framework import serializers


class UserHomeworkSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели выполненной домашней работы
    """

    class Meta:
        model = UserHomework
        fields = "__all__"


class UserHomeworkStatisticsSerializer(serializers.Serializer):
    """
    Сериализатор для статистики по сданным домашним заданиям
    """

    start_date = serializers.DateField(help_text="С какой даты показать записи", default=date(2014, 1, 1),
                                       required=False)
    end_date = serializers.DateField(help_text="До какой даты показать записи", required=False,
                                     default=date(2200, 1, 1))
    status = serializers.CharField(max_length=20, help_text="Статус работы", required=False,
                                   default=None)
    start_mark = serializers.IntegerField(help_text="Оценка от",
                                          required=False)
    end_mark = serializers.IntegerField(help_text="Оценка до",
                                        required=False)
    course_id = serializers.IntegerField(help_text="Id курса",
                                         default=None,
                                         required=False)
    group_id = serializers.IntegerField(help_text="Id группы",
                                        required=False,
                                        default=None)
    homework_id = serializers.IntegerField(help_text="Id домашней работы",
                                           required=False,
                                           default=None)
    class Meta:
        fields = '__all__'
