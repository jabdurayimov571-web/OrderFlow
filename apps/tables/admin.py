from django.contrib import admin
from django.utils.html import format_html

from .models import Table


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("number", "qr_token", "is_active")
    list_filter = ("is_active",)
    readonly_fields = ("qr_token", "qr_url", "qr_preview")
    fields = ("number", "is_active", "qr_token", "qr_url", "qr_preview")

    @admin.display(description="Menyu URL")
    def qr_url(self, obj):
        return obj.menu_url if obj.pk else "-"

    @admin.display(description="QR kod")
    def qr_preview(self, obj):
        if not obj.pk:
            return "Saqlangach QR paydo bo'ladi"
        return format_html(
            '<img src="data:image/png;base64,{}" style="width:180px;height:180px;" />',
            obj.qr_png_base64(),
        )
