from django.contrib import admin

from lesson_tests.models import LessonTest


@admin.register(LessonTest)
class LessonTestAdmin(admin.ModelAdmin):
    pass
