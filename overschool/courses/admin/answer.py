from django.contrib import admin

from courses.models import Answer


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    pass
