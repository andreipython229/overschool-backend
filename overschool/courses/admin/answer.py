from courses.models import Answer
from django.contrib import admin


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    pass
