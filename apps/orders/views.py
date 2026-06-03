from rest_framework import generics, status
from rest_framework.response import Response

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
