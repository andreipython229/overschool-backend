from django.contrib import admin
from .models import MainCourseModel


class MainCourseModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'course_text']


admin.site.register(MainCourseModel, MainCourseModelAdmin)
# Register your models here.
