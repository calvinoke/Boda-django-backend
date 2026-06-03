from rest_framework.permissions import BasePermission


# =========================================================
# MANAGEMENT ROLES
# =========================================================

MANAGEMENT_ROLES = (
    "super_admin",
    "stage_chairman",
    "stage_secretary",
    "stage_defense",
)


# =========================================================
# CAN ISSUE FINE
# =========================================================

class CanIssueFine(BasePermission):

    message = "You do not have permission to issue fines."

    def has_permission(self, request, view):

        return (
            request.user.is_authenticated
            and getattr(request.user, "role", None) in MANAGEMENT_ROLES
        )


# =========================================================
# CAN VIEW FINES
# =========================================================

class CanViewFines(BasePermission):

    message = "Authentication is required."

    def has_permission(self, request, view):

        return request.user.is_authenticated