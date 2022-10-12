from courses.models import Homework
from django.contrib import admin


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    pass
