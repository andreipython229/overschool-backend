from django.contrib import admin

from .models import APIRequestLog


class APIRequestLogAdmin(admin.ModelAdmin):
    date_hierarchy = "requested_at"
    list_display = (
        "id",
        "requested_at",
        "response_ms",
        "status_code",
        "user",
        "method",
        "path",
        "remote_addr",
        "host",
        "query_params",
    )
    list_filter = ("method", "status_code")
    search_fields = (
        "path",
        "user__email",
    )
    raw_id_fields = ("user",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False



admin.site.register(APIRequestLog, APIRequestLogAdmin)
