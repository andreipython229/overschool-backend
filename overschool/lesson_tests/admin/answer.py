from django.contrib import admin
from lesson_tests.models import Answer


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    pass
