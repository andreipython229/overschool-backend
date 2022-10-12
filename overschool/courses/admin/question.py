from courses.models import Question
from django.contrib import admin


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    pass
