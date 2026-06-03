from rest_framework.permissions import BasePermission


class IsCashier(BasePermission):
    """Faqat kassir yoki admin/superuser kira oladi."""

    message = "Bu amal uchun kassir huquqi kerak."

    def has_permission(self, request, view):
        u = request.user
        return bool(
            u and u.is_authenticated and (u.is_kassir or u.role == "admin" or u.is_superuser)
        )


class IsKitchen(BasePermission):
    """Faqat oshpaz yoki admin/superuser kira oladi."""

    message = "Bu amal uchun oshpaz huquqi kerak."

    def has_permission(self, request, view):
        u = request.user
        return bool(
            u and u.is_authenticated and (u.is_oshpaz or u.role == "admin" or u.is_superuser)
        )


class IsAdmin(BasePermission):
    """Faqat admin yoki superuser kira oladi."""

    message = "Bu amal uchun admin huquqi kerak."

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and (u.role == "admin" or u.is_superuser))
