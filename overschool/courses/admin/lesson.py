from django.contrib import admin

from courses.models import Lesson


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["lesson_id", "section", "name", "description", "video", "order"]
