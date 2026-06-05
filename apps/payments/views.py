"""To'lov endpoint'lari.

- PaymeWebhookView: Payme serveri chaqiradigan JSON-RPC webhook (Basic auth).
- PaymeCheckoutURLView: mijozga Payme to'lov sahifasi URL'ini beradi.

Webhook'lar tashqi serverdan keladi, shuning uchun auth qo'lda (provayder
protokoli bo'yicha) tekshiriladi; DRF SessionAuth ishlatilmagani uchun CSRF
talab qilinmaydi.
"""

import base64
import hmac
import json

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.models import Order

from . import click as click_api
from . import payme as payme_api

# JSON-RPC metod nomi -> PaymeService metodi
PAYME_METHODS = {
    "CheckPerformTransaction": "check_perform_transaction",
    "CreateTransaction": "create_transaction",
    "PerformTransaction": "perform_transaction",
    "CancelTransaction": "cancel_transaction",
    "CheckTransaction": "check_transaction",
    "GetStatement": "get_statement",
}


def _payme_auth_ok(request):
    """Authorization: Basic base64('Paycom:<merchant_key>') ni tekshiradi."""
    header = request.META.get("HTTP_AUTHORIZATION", "")
    if not header.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(header[6:]).decode()
    except Exception:
        return False
    if ":" not in decoded:
        return False
    _, key = decoded.split(":", 1)
    expected = settings.PAYME_MERCHANT_KEY
    # Kalit sozlanmagan bo'lsa (bo'sh) auth har doim rad etiladi.
    return bool(expected) and hmac.compare_digest(key, expected)


class PaymeWebhookView(APIView):
    """POST /api/payments/payme/ — Payme JSON-RPC webhook."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        req_id = None
        try:
            try:
                data = json.loads(request.body.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                raise payme_api.PaymeError(
                    payme_api.ERR_PARSE,
                    payme_api._msg("JSON o'qib bo'lmadi", "Ошибка разбора JSON", "Parse error"),
                )
            req_id = data.get("id")

            if not _payme_auth_ok(request):
                raise payme_api.PaymeError(
                    payme_api.ERR_INSUFFICIENT_PRIVILEGE,
                    payme_api._msg("Ruxsat yetarli emas", "Недостаточно привилегий", "Insufficient privileges"),
                )

            handler_name = PAYME_METHODS.get(data.get("method"))
            if not handler_name:
                raise payme_api.PaymeError(
                    payme_api.ERR_METHOD_NOT_FOUND,
                    payme_api._msg("Metod topilmadi", "Метод не найден", "Method not found"),
                )

            params = data.get("params") or {}
            service = payme_api.PaymeService()
            with transaction.atomic():
                result = getattr(service, handler_name)(params)
            return Response({"jsonrpc": "2.0", "id": req_id, "result": result})

        except payme_api.PaymeError as e:
            error = {"code": e.code, "message": e.message}
            if e.data is not None:
                error["data"] = e.data
            return Response({"jsonrpc": "2.0", "id": req_id, "error": error})
        except Exception:
            return Response(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": payme_api.ERR_SYSTEM,
                        "message": payme_api._msg("Tizim xatosi", "Системная ошибка", "System error"),
                    },
                }
            )


class PaymeCheckoutURLView(APIView):
    """GET /api/payments/<public_id>/payme-url/ — to'lov sahifasi URL'i."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, public_id):
        order = get_object_or_404(Order, public_id=public_id)
        if order.payment_method != Order.PaymentMethod.ONLINE:
            return Response({"detail": "Bu zakaz online to'lov uchun emas."}, status=400)
        if not settings.PAYME_MERCHANT_ID:
            return Response({"detail": "Payme sozlanmagan."}, status=503)
        return Response({"url": payme_api.build_payme_checkout_url(order)})


class ClickPrepareView(APIView):
    """POST /api/payments/click/prepare/ — Click action=0."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        if hasattr(data, "dict"):
            data = data.dict()
        with transaction.atomic():
            return Response(click_api.ClickService().prepare(data))


class ClickCompleteView(APIView):
    """POST /api/payments/click/complete/ — Click action=1."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        if hasattr(data, "dict"):
            data = data.dict()
        with transaction.atomic():
            return Response(click_api.ClickService().complete(data))


class ClickCheckoutURLView(APIView):
    """GET /api/payments/<public_id>/click-url/ — to'lov sahifasi URL'i."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, public_id):
        order = get_object_or_404(Order, public_id=public_id)
        if order.payment_method != Order.PaymentMethod.ONLINE:
            return Response({"detail": "Bu zakaz online to'lov uchun emas."}, status=400)
        if not settings.CLICK_SERVICE_ID:
            return Response({"detail": "Click sozlanmagan."}, status=503)
        return Response({"url": click_api.build_click_checkout_url(order)})
