from django.contrib import admin
from schools.models import School, Tariff


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    pass


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    pass
