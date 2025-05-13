from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Pozwala tylko właścicielowi faktury lub administratorowi na dostęp.
    """

    def has_object_permission(self, request, view, obj):
        # Dla adminów pozwalamy zawsze
        if request.user and request.user.is_staff:
            return True

        # Pozwalamy tylko jeśli użytkownik jest twórcą
        return obj.created_by == request.user


class IsSelfOrAdmin(permissions.BasePermission):
    """
    Pozwala właścicielowi (user=object.user) lub administratorowi.
    """

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user == request.user