from rest_framework import serializers

from .models import User # Course, Section, Lesson, Test, Question, Answer, Homework, UserHomework, UserTest


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('__all__')
#
#
# class CourseSerializer(serializers.ModelSerializer):
#     """
#     Сериализатор модели курса
#     """
#
#     class Meta:
#         model = Course
#         fields = '__all__'
#
#
# class SectionSerializer(serializers.ModelSerializer):
#     """
#     Сериализатор модели раздела
#     """
#
#     class Meta:
#         model = Section
#         fields = '__all__'
#
#
# class LessonSerializer(serializers.ModelSerializer):
#     """
#     Сериализатор модели урока
#     """
#
#     class Meta:
#         model = Lesson
#         fields = '__all__'
#
#
# class TestSerializer(serializers.ModelSerializer):
#     """
#     Сериализатор модели теста
#     """
#
#     class Meta:
#         model = Test
#         fields = '__all__'
#
#
# class QuestionSerializer(serializers.ModelSerializer):
#     """
#     Сериализатор модели вопроса
#     """
#
#     class Meta:
#         model = Question
#         fields = '__all__'
#
#
# class AnswerSerializer(serializers.ModelSerializer):
#     """
#     Сериализатор модели ответа
#     """
#
#     class Meta:
#         model = Answer
#         fields = '__all__'
#
#
# class HomeWorkSerializer(serializers.ModelSerializer):
#     """
#     Сериализатор моедли домашнего задания
#     """
#
#     class Meta:
#         model = Homework
#         fields = '__all__'
#
#
# class UserHomeWork(serializers.ModelSerializer):
#     """
#     Сериализатор модели выполненной домашней работы
#     """
#
#     class Meta:
#         model = UserHomework
#         fields = '__all__'
#
#
# class UserTestSerializer(serializers.ModelSerializer):
#     """
#     Сериализатор модели выполненного теста
#     """
#
#     class Meta:
#         model = UserTest
#         fields = '__all__'
