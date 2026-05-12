from rest_framework.permissions import BasePermission


MANAGEMENT_ROLES = [
    'super_admin',
    'stage_chairman',
    'stage_secretary',
    'stage_defense',
]


class CanIssueFine(BasePermission):

    def has_permission(self, request, view):

        return (
            request.user.is_authenticated and
            request.user.role in MANAGEMENT_ROLES
        )


class CanViewFines(BasePermission):

    def has_permission(self, request, view):

        return request.user.is_authenticated