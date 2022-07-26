from rest_framework import permissions, request


class IsAnonymous(permissions.BasePermission):
    def has_permission(self, request: request.HttpRequest, view):
        return bool(request.user and request.user.is_anonymous)
