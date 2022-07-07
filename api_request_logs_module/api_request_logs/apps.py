from django.apps import AppConfig


class ApiRequestLogsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api_request_logs"
    verbose_name = 'API request logs'
