from django.contrib import admin

from .models import ClickTransaction, PaymeTransaction


@admin.register(PaymeTransaction)
class PaymeTransactionAdmin(admin.ModelAdmin):
    list_display = ("transaction_id", "order", "amount_som", "state", "created_at")
    list_filter = ("state",)
    search_fields = ("transaction_id", "order__number")
    readonly_fields = (
        "order",
        "transaction_id",
        "amount",
        "state",
        "reason",
        "create_time",
        "perform_time",
        "cancel_time",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        # Tranzaksiyalar faqat provayder webhook orqali yaratiladi.
        return False


@admin.register(ClickTransaction)
class ClickTransactionAdmin(admin.ModelAdmin):
    list_display = ("click_trans_id", "order", "amount", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("click_trans_id", "click_paydoc_id", "order__number")
    readonly_fields = (
        "order",
        "click_trans_id",
        "click_paydoc_id",
        "amount",
        "status",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False
