from django.contrib import admin
from schools.models import Referral, ReferralClick


@admin.register(Referral)
class SchoolReferralAdmin(admin.ModelAdmin):
    pass


@admin.register(ReferralClick)
class SchoolReferralClickAdmin(admin.ModelAdmin):
    pass
