from datetime import timedelta

from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdmin
from apps.orders.models import Order, OrderItem

# To'langan (kassa/oshpazdan o'tgan) zakazlar
PAID_STATUSES = [Order.Status.PREPARING, Order.Status.READY, Order.Status.COMPLETED]


class AnalyticsSummaryView(APIView):
    """Admin uchun analitika: savdo, zakazlar, top taomlar, oxirgi 7 kun."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdmin]

    def get(self, request):
        today = timezone.now().date()
        orders = Order.objects.all()
        paid = orders.filter(status__in=PAID_STATUSES)

        def money_sum(qs):
            return float(qs.aggregate(s=Sum("total"))["s"] or 0)

        by_status = {
            row["status"]: row["c"]
            for row in orders.values("status").annotate(c=Count("id"))
        }

        top_items = list(
            OrderItem.objects.exclude(order__status=Order.Status.CANCELLED)
            .values("name")
            .annotate(qty=Sum("quantity"), revenue=Sum("line_total"))
            .order_by("-qty")[:5]
        )
        for it in top_items:
            it["revenue"] = float(it["revenue"] or 0)

        last_7_days = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            last_7_days.append({
                "date": d.isoformat(),
                "orders": orders.filter(created_at__date=d).count(),
                "revenue": money_sum(paid.filter(created_at__date=d)),
            })

        paid_count = paid.count()
        return Response({
            "orders_total": orders.count(),
            "orders_today": orders.filter(created_at__date=today).count(),
            "revenue_total": money_sum(paid),
            "revenue_today": money_sum(paid.filter(created_at__date=today)),
            "avg_check": round(money_sum(paid) / paid_count, 2) if paid_count else 0,
            "by_status": by_status,
            "top_items": top_items,
            "last_7_days": last_7_days,
        })
