from django.contrib import admin

from courses.models import Homework


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    pass
