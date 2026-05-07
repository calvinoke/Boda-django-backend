from rest_framework.permissions import BasePermission


class IsAdminUserRole(BasePermission):

    def has_permission(self, request, view):

        return request.user.role == 'admin'


class IsRiderOwner(BasePermission):

    def has_object_permission(self, request, view, obj):

        return obj.user == request.user




class IsAdminRole(BasePermission):

    def has_permission(self, request, view):

        return (
            request.user.is_authenticated and
            request.user.role == 'admin'
        )