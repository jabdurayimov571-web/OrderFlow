from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsCashier, IsKitchen
from apps.notifications.services import send_order_ready_push

from .models import Order
from .serializers import OrderCreateSerializer, OrderReadSerializer


class OrderCreateView(generics.CreateAPIView):
    """Mijoz zakaz beradi: POST /api/orders/"""

    serializer_class = OrderCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        read = OrderReadSerializer(order, context=self.get_serializer_context())
        return Response(read.data, status=status.HTTP_201_CREATED)


class OrderStatusView(generics.RetrieveAPIView):
    """Mijoz zakaz holatini ko'radi: GET /api/orders/<public_id>/"""

    queryset = Order.objects.all().prefetch_related("items__modifiers")
    serializer_class = OrderReadSerializer
    lookup_field = "public_id"
    lookup_url_kwarg = "public_id"


class CashierOrderListView(generics.ListAPIView):
    """Kassir: to'lov kutilayotgan zakazlar (tarkib + narx bilan)."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsCashier]
    serializer_class = OrderReadSerializer

    def get_queryset(self):
        return (
            Order.objects.filter(status=Order.Status.AWAITING_PAYMENT)
            .prefetch_related("items__modifiers")
            .order_by("created_at")
        )


class CashierConfirmPaymentView(APIView):
    """Kassir to'lovni tasdiqlaydi -> zakaz TAYYORLANMOQDA ga o'tadi (oshpazga tushadi)."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsCashier]

    def post(self, request, public_id):
        order = get_object_or_404(Order, public_id=public_id, status=Order.Status.AWAITING_PAYMENT)
        order.payment_status = Order.PaymentStatus.PAID
        order.status = Order.Status.PREPARING
        order.save(update_fields=["payment_status", "status", "updated_at"])
        return Response(OrderReadSerializer(order).data)


class KitchenOrderListView(generics.ListAPIView):
    """Oshpaz: tayyorlanayotgan zakazlar (eng eskisi birinchi)."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsKitchen]
    serializer_class = OrderReadSerializer

    def get_queryset(self):
        return (
            Order.objects.filter(status=Order.Status.PREPARING)
            .prefetch_related("items__modifiers")
            .order_by("created_at")
        )


class KitchenMarkReadyView(APIView):
    """Oshpaz zakazni TAYYOR deb belgilaydi (mijozga keyin xabar boradi)."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsKitchen]

    def post(self, request, public_id):
        order = get_object_or_404(Order, public_id=public_id, status=Order.Status.PREPARING)
        order.status = Order.Status.READY
        order.save(update_fields=["status", "updated_at"])
        send_order_ready_push(order)  # mijozga push (xato bo'lsa ham READY qoladi)
        return Response(OrderReadSerializer(order).data)
