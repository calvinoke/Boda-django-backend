from rest_framework.permissions import BasePermission


# =========================================================
# MANAGEMENT ROLES
# =========================================================

MANAGEMENT_ROLES = [

    'super_admin',

    'stage_chairman',

    'stage_secretary',

    'stage_defense',
]


# =========================================================
# MANAGEMENT ACCESS ONLY
# =========================================================

class IsManagementRole(BasePermission):

    def has_permission(self, request, view):

        return (

            request.user.is_authenticated and

            request.user.role in MANAGEMENT_ROLES
        )


# =========================================================
# RIDER OWNER ONLY
# =========================================================

class IsRiderOwner(BasePermission):

    def has_object_permission(self, request, view, obj):

        # USER OBJECT
        if hasattr(obj, 'id') and obj == request.user:

            return True

        # MODELS WITH USER FIELD
        if hasattr(obj, 'user'):

            return obj.user == request.user

        return False


# =========================================================
# MANAGEMENT OR OWNER
# =========================================================

class IsManagementOrOwner(BasePermission):

    def has_object_permission(self, request, view, obj):

        # MANAGEMENT HAS FULL ACCESS
        if (

            request.user.is_authenticated and

            request.user.role in MANAGEMENT_ROLES
        ):

            return True

        # USER OBJECT
        if obj == request.user:

            return True

        # MODELS WITH USER FIELD
        if hasattr(obj, 'user'):

            return obj.user == request.user

        return False


# =========================================================
# GUEST RIDER VIEW ONLY
# =========================================================

class IsGuestRiderReadOnly(BasePermission):

    def has_permission(self, request, view):

        return (

            request.user.is_authenticated and

            request.user.role == 'guest_rider' and

            request.method in ['GET', 'HEAD', 'OPTIONS']
        )


# =========================================================
# RIDER SELF UPDATE ONLY
# =========================================================

class IsRiderSelfUpdate(BasePermission):

    def has_permission(self, request, view):

        return (

            request.user.is_authenticated and

            request.user.role == 'rider'
        )

    def has_object_permission(self, request, view, obj):

        # ONLY OWNER
        if hasattr(obj, 'user'):

            return obj.user == request.user

        return obj == request.user