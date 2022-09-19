from django.contrib.auth import get_user_model
from rest_framework import permissions


class OwnerProfilePermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or (
            request.user == get_user_model().objects.get(pk=view.kwargs["id"])
            and request.method in (*permissions.SAFE_METHODS, "PUT", "PATCH")
        )
