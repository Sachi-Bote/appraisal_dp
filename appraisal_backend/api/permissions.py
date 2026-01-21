from rest_framework.permissions import BasePermission


class IsRole(BasePermission):
    """
    Base role permission.
    Child classes must define allowed_roles.
    """
    allowed_roles = []

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in self.allowed_roles
        )


# =========================
# SPECIFIC ROLE PERMISSIONS
# =========================

class IsFaculty(IsRole):
    allowed_roles = ["FACULTY"]


class IsHOD(IsRole):
    allowed_roles = ["HOD"]


class IsPrincipal(IsRole):
    allowed_roles = ["PRINCIPAL"]


class IsAdmin(IsRole):
    allowed_roles = ["ADMIN"]
