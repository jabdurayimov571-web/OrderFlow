from rest_framework import viewsets

from .models import Category, MenuItem
from .serializers import CategorySerializer, MenuItemSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Faol kategoriyalar + ularning mavjud taomlari (mijoz menyusi uchun)."""

    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(is_active=True).prefetch_related(
            "items__modifiers"
        )


class MenuItemViewSet(viewsets.ReadOnlyModelViewSet):
    """Barcha mavjud taomlar (ixtiyoriy ?category=<id> filtri bilan)."""

    serializer_class = MenuItemSerializer

    def get_queryset(self):
        qs = MenuItem.objects.filter(is_available=True).prefetch_related("modifiers")
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category_id=category)
        return qs
