from rest_framework import permissions, request


class IsTeacher(permissions.BasePermission):
    def has_permission(self, request: request.HttpRequest, view):
        return bool(request.user and "Teacher" in request.user.groups.values_list("name", flat=True))
