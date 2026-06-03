from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.models import Order

from .models import PushSubscription


class VapidKeyView(APIView):
    """Frontend uchun VAPID public kalit (applicationServerKey)."""

    def get(self, request):
        return Response({"public_key": settings.VAPID_PUBLIC_KEY})


class SubscribeView(APIView):
    """Mijozning push obunasini zakazga bog'lab saqlaydi."""

    def post(self, request):
        order_public_id = request.data.get("order")
        sub = request.data.get("subscription") or {}
        endpoint = sub.get("endpoint")
        keys = sub.get("keys") or {}
        if not (order_public_id and endpoint and keys.get("p256dh") and keys.get("auth")):
            return Response({"detail": "Noto'g'ri obuna ma'lumoti."}, status=400)

        order = get_object_or_404(Order, public_id=order_public_id)
        PushSubscription.objects.get_or_create(
            order=order,
            endpoint=endpoint,
            defaults={"p256dh": keys["p256dh"], "auth": keys["auth"]},
        )
        return Response({"ok": True}, status=201)
