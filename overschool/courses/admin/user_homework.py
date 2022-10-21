from django.contrib import admin

from courses.models import UserHomework


@admin.register(UserHomework)
class UserHomeworkAdmin(admin.ModelAdmin):
    pass
