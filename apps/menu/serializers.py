from rest_framework import serializers

from .models import Category, MenuItem, Modifier


class ModifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modifier
        fields = ["id", "name", "price_delta"]


class MenuItemSerializer(serializers.ModelSerializer):
    modifiers = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = [
            "id",
            "name",
            "description",
            "price",
            "image",
            "is_available",
            "modifiers",
        ]

    def get_modifiers(self, obj):
        active = obj.modifiers.filter(is_active=True)
        return ModifierSerializer(active, many=True).data


class CategorySerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "items"]

    def get_items(self, obj):
        available = obj.items.filter(is_available=True)
        return MenuItemSerializer(available, many=True, context=self.context).data
