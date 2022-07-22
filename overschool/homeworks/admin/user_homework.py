from django.contrib import admin
from homeworks.models import UserHomework


@admin.register(UserHomework)
class UserHomeworkAdmin(admin.ModelAdmin):
    pass
