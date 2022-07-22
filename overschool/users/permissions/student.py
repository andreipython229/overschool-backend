from rest_framework import permissions, request


class IsStudent(permissions.BasePermission):
    def has_permission(self, request: request.HttpRequest, view):
        return bool(request.user and "Student" in request.user.groups.values_list("name", flat=True))
