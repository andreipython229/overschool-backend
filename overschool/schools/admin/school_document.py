from django.contrib import admin
from schools.models import SchoolDocuments


@admin.register(SchoolDocuments)
class DocumentsAdmin(admin.ModelAdmin):
    pass
