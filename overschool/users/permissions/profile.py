from django.contrib.auth import get_user_model
from rest_framework import permissions


class OwnerProfilePermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            "pk" in view.kwargs
            and request.user == get_user_model().objects.get(profile=view.kwargs["pk"])
            and request.method in (*permissions.SAFE_METHODS, "PUT", "PATCH")
        ) or request.method in permissions.SAFE_METHODS
