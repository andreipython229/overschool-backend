from django.contrib import admin
from schools.models import Banner, BannerAccept, BannerClick


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    pass


@admin.register(BannerClick)
class BannerClickAdmin(admin.ModelAdmin):
    pass


@admin.register(BannerAccept)
class BannerAcceptAdmin(admin.ModelAdmin):
    pass
