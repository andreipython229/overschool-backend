from django.contrib import admin
from schools.models import SchoolBranding


@admin.register(SchoolBranding)
class SchoolBrandingAdmin(admin.ModelAdmin):
    pass
