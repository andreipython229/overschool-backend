from courses.models import UserHomework
from django.contrib import admin


@admin.register(UserHomework)
class UserHomeworkAdmin(admin.ModelAdmin):
    pass
