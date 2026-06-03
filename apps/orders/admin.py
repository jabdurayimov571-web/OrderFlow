from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("name", "quantity", "unit_price", "line_total", "note")
    readonly_fields = fields
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "table",
        "status",
        "payment_method",
        "payment_status",
        "total",
        "created_at",
    )
    list_filter = ("status", "payment_method", "payment_status")
    search_fields = ("number",)
    readonly_fields = ("public_id", "number", "total", "created_at", "updated_at")
    inlines = [OrderItemInline]
