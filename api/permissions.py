from rest_framework import permissions

class IsInApiGroup(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='api').exists()