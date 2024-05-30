from django.contrib import admin

from schools.models import Domain


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ('domain_name', 'user', 'nginx_configured', 'created_at')
    list_filter = ('nginx_configured',)
    search_fields = ('domain_name',)
