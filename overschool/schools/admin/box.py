from common_services.selectel_client import UploadToS3
from django.contrib import admin
from schools.models import Box, BoxPrize, Payment, Prize, UserPrize

s3 = UploadToS3()


@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "quantity",
        "bonus_quantity",
        "is_active",
        "auto_deactivation_time",
    )
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Prize)
class PrizeAdmin(admin.ModelAdmin):
    list_display = ("name", "drop_chance", "guaranteed_box_count", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(BoxPrize)
class BoxPrizeAdmin(admin.ModelAdmin):
    list_display = ("box", "prize")
    search_fields = ("box__name", "prize__name")


@admin.register(UserPrize)
class UserPrizeAdmin(admin.ModelAdmin):
    list_display = ("user", "prize")
    search_fields = ("user__email", "prize__name")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("user", "box", "amount", "payment_status", "created_at")
    list_filter = ("payment_status", "created_at")
    search_fields = ("user__username", "box__name")
