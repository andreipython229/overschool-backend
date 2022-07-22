from django.contrib import admin
from lesson_tests.models import Question


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    pass
