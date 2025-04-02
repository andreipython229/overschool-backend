from django.contrib import admin
from schools.models import InviteProgram


@admin.register(InviteProgram)
class InviteProgramAdmin(admin.ModelAdmin):
    pass


