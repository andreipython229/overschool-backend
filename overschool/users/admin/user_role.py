from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group
from users.models import UserRole, UserSchoolDocuments

admin.site.unregister(Group)


@admin.register(UserRole)
class UserRoleAdmin(GroupAdmin):
    pass


@admin.register(UserSchoolDocuments)
class DocumentsAdmin(admin.ModelAdmin):
    pass
