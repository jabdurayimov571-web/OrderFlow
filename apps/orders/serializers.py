from django.db import transaction
from rest_framework import serializers

from apps.menu.models import MenuItem, Modifier
from apps.tables.models import Table

from .models import Order, OrderItem


# ---------- O'qish (javob) ----------
class OrderItemReadSerializer(serializers.ModelSerializer):
    modifiers = serializers.StringRelatedField(many=True)

    class Meta:
        model = OrderItem
        fields = ["id", "name", "unit_price", "quantity", "modifiers", "line_total", "note"]


class OrderReadSerializer(serializers.ModelSerializer):
    items = OrderItemReadSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    table_number = serializers.IntegerField(source="table.number", read_only=True)

    class Meta:
        model = Order
        fields = [
            "public_id",
            "number",
            "table_number",
            "status",
            "status_display",
            "payment_method",
            "payment_status",
            "total",
            "customer_note",
            "items",
            "created_at",
        ]


# ---------- Yaratish (so'rov) ----------
class OrderItemCreateSerializer(serializers.Serializer):
    menu_item = serializers.PrimaryKeyRelatedField(
        queryset=MenuItem.objects.filter(is_available=True)
    )
    quantity = serializers.IntegerField(min_value=1, default=1)
    modifiers = serializers.PrimaryKeyRelatedField(
        queryset=Modifier.objects.filter(is_active=True), many=True, required=False
    )
    note = serializers.CharField(max_length=255, required=False, allow_blank=True)


class OrderCreateSerializer(serializers.Serializer):
    table_token = serializers.UUIDField()
    payment_method = serializers.ChoiceField(
        choices=Order.PaymentMethod.choices, default=Order.PaymentMethod.CASH
    )
    note = serializers.CharField(required=False, allow_blank=True)
    items = OrderItemCreateSerializer(many=True)

    def validate_table_token(self, value):
        try:
            self._table = Table.objects.get(qr_token=value, is_active=True)
        except Table.DoesNotExist:
            raise serializers.ValidationError("Stol topilmadi yoki faol emas.")
        return value

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Savat bo'sh bo'lishi mumkin emas.")
        return value

    def create(self, validated_data):
        items_data = validated_data["items"]
        payment_method = validated_data["payment_method"]
        # Naqd -> kassaga (to'lov kutilmoqda); online -> Phase 8 to'lovdan keyin tayyorlashga
        status = (
            Order.Status.AWAITING_PAYMENT
            if payment_method == Order.PaymentMethod.CASH
            else Order.Status.CREATED
        )
        with transaction.atomic():
            order = Order.objects.create(
                table=self._table,
                payment_method=payment_method,
                customer_note=validated_data.get("note", ""),
                status=status,
            )
            total = 0
            for it in items_data:
                menu_item = it["menu_item"]
                qty = it["quantity"]
                mods = it.get("modifiers", [])
                mod_sum = sum((m.price_delta for m in mods), 0)
                line_total = (menu_item.price + mod_sum) * qty
                order_item = OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    name=menu_item.name,
                    unit_price=menu_item.price,
                    quantity=qty,
                    line_total=line_total,
                    note=it.get("note", ""),
                )
                if mods:
                    order_item.modifiers.set(mods)
                total += line_total
            order.total = total
            order.save(update_fields=["total"])
        return order
