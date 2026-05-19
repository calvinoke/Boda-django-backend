from rest_framework.permissions import BasePermission, SAFE_METHODS


# =========================================================
# ROLES
# =========================================================

MANAGEMENT_ROLES = [
    'super_admin',
    'stage_chairman',
    'stage_secretary',
    'stage_defense',
]


# =========================================================
# MANAGEMENT ONLY
# =========================================================

class IsManagementRole(BasePermission):

    def has_permission(self, request, view):

        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'role') and
            request.user.role in MANAGEMENT_ROLES
        )


# =========================================================
# ADMIN ONLY
# =========================================================

class IsAdminRole(BasePermission):

    def has_permission(self, request, view):

        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'role') and
            request.user.role == 'super_admin'
        )


# =========================================================
# MANAGEMENT OR READ-ONLY ACCESS
# =========================================================

class IsManagementOrReadOnly(BasePermission):

    def has_permission(self, request, view):

        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated

        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'role') and
            request.user.role in MANAGEMENT_ROLES
        )


# =========================================================
# RIDER OWNER
# =========================================================

class IsRiderOwner(BasePermission):

    def has_object_permission(self, request, view, obj):

        if hasattr(obj, 'user'):
            return obj.user == request.user

        return obj == request.user


# =========================================================
# MANAGEMENT OR OWNER
# =========================================================

class IsManagementOrOwner(BasePermission):

    def has_object_permission(self, request, view, obj):

        if (
            request.user.is_authenticated and
            hasattr(request.user, 'role') and
            request.user.role in MANAGEMENT_ROLES
        ):
            return True

        if hasattr(obj, 'user'):
            return obj.user == request.user

        return obj == request.user