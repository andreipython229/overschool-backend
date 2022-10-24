from django.contrib import admin

from courses.models import Question


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    pass
