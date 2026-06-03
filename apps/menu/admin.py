from django.contrib import admin
from django.utils.html import format_html

from .models import Category, MenuItem, Modifier


class ModifierInline(admin.TabularInline):
    model = Modifier
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "sort_order", "is_active")
    list_editable = ("sort_order", "is_active")
    search_fields = ("name",)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "is_available", "image_preview")
    list_filter = ("category", "is_available")
    list_editable = ("price", "is_available")
    search_fields = ("name", "description")
    inlines = [ModifierInline]
    readonly_fields = ("image_preview",)

    @admin.display(description="Rasm")
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:40px;border-radius:4px;" />',
                obj.image.url,
            )
        return "-"
