from courses.models import Lesson
from django.contrib import admin


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    pass
