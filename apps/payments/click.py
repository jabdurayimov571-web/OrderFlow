"""Click SHOP API — Prepare/Complete (form POST, md5 imzo).

Click serveri ikki bosqichda chaqiradi:
  action=0 (Prepare)  -> to'lovni tekshirish, ClickTransaction yaratish
  action=1 (Complete) -> to'lovni yakunlash, zakaz PREPARING ga o'tadi

Imzo (sign_string) — md5, SECRET_KEY o'rtada:
  Prepare:  click_trans_id + service_id + KEY + merchant_trans_id +
            amount + action + sign_time
  Complete: click_trans_id + service_id + KEY + merchant_trans_id +
            merchant_prepare_id + amount + action + sign_time

Hujjat: https://docs.click.uz/en/click-api-request/
"""

import hashlib
import hmac
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError

from apps.orders.models import Order

from .models import ClickTransaction

# --- Xato kodlari (rasmiy protokol) ---
ERR_SUCCESS = 0
ERR_SIGN = -1
ERR_INCORRECT_AMOUNT = -2
ERR_ACTION_NOT_FOUND = -3
ERR_ALREADY_PAID = -4
ERR_ORDER_NOT_FOUND = -5  # "user/order does not exist"
ERR_TRANS_NOT_FOUND = -6
ERR_FAILED_TO_UPDATE = -7
ERR_BAD_REQUEST = -8
ERR_TRANS_CANCELLED = -9


def _md5(raw):
    return hashlib.md5(raw.encode()).hexdigest()


def prepare_signature(d, secret):
    return _md5(
        f"{d.get('click_trans_id', '')}{d.get('service_id', '')}{secret}"
        f"{d.get('merchant_trans_id', '')}{d.get('amount', '')}"
        f"{d.get('action', '')}{d.get('sign_time', '')}"
    )


def complete_signature(d, secret):
    return _md5(
        f"{d.get('click_trans_id', '')}{d.get('service_id', '')}{secret}"
        f"{d.get('merchant_trans_id', '')}{d.get('merchant_prepare_id', '')}"
        f"{d.get('amount', '')}{d.get('action', '')}{d.get('sign_time', '')}"
    )


def build_click_checkout_url(order):
    """Mijozni Click to'lov sahifasiga yo'naltiruvchi URL."""
    params = {
        "service_id": settings.CLICK_SERVICE_ID,
        "merchant_id": settings.CLICK_MERCHANT_ID,
        "amount": str(order.total),
        "transaction_param": str(order.public_id),
        "return_url": f"{settings.SITE_URL}/t/{order.table.qr_token}/",
    }
    return f"{settings.CLICK_PAY_URL}?{urlencode(params)}"


class ClickService:
    """Prepare/Complete mantig'i. Har biri Click kutadigan javob dict'ini qaytaradi."""

    def _resp(self, d, error, note, extra=None):
        out = {
            "click_trans_id": d.get("click_trans_id"),
            "merchant_trans_id": d.get("merchant_trans_id"),
            "error": error,
            "error_note": note,
        }
        if extra:
            out.update(extra)
        return out

    def _find_order(self, merchant_trans_id):
        if not merchant_trans_id:
            return None
        try:
            return Order.objects.get(public_id=merchant_trans_id)
        except (Order.DoesNotExist, DjangoValidationError, ValueError):
            return None

    def _amount_ok(self, order, amount):
        try:
            return Decimal(str(amount)) == order.total
        except (InvalidOperation, TypeError):
            return False

    def _cancel_order(self, order):
        if order.status == Order.Status.CREATED:
            order.status = Order.Status.CANCELLED
            order.save(update_fields=["status", "updated_at"])

    # --- action=0 ---
    def prepare(self, d):
        if not hmac.compare_digest(
            prepare_signature(d, settings.CLICK_SECRET_KEY), d.get("sign_string", "") or ""
        ):
            return self._resp(d, ERR_SIGN, "Imzo tekshiruvi muvaffaqiyatsiz")

        order = self._find_order(d.get("merchant_trans_id"))
        if order is None:
            return self._resp(d, ERR_ORDER_NOT_FOUND, "Zakaz topilmadi")
        if order.payment_status == Order.PaymentStatus.PAID:
            return self._resp(d, ERR_ALREADY_PAID, "Zakaz allaqachon to'langan")
        if (
            order.payment_method != Order.PaymentMethod.ONLINE
            or order.status != Order.Status.CREATED
        ):
            return self._resp(d, ERR_ORDER_NOT_FOUND, "Zakaz to'lovga mos emas")
        if not self._amount_ok(order, d.get("amount")):
            return self._resp(d, ERR_INCORRECT_AMOUNT, "Noto'g'ri summa")

        txn, _ = ClickTransaction.objects.get_or_create(
            click_trans_id=d.get("click_trans_id"),
            order=order,
            defaults={
                "amount": Decimal(str(d.get("amount"))),
                "click_paydoc_id": d.get("click_paydoc_id", "") or "",
                "status": ClickTransaction.Status.PREPARED,
            },
        )
        return self._resp(d, ERR_SUCCESS, "Success", extra={"merchant_prepare_id": txn.id})

    # --- action=1 ---
    def complete(self, d):
        if not hmac.compare_digest(
            complete_signature(d, settings.CLICK_SECRET_KEY), d.get("sign_string", "") or ""
        ):
            return self._resp(d, ERR_SIGN, "Imzo tekshiruvi muvaffaqiyatsiz")

        try:
            txn = ClickTransaction.objects.select_for_update().get(
                pk=d.get("merchant_prepare_id")
            )
        except (ClickTransaction.DoesNotExist, ValueError, TypeError):
            return self._resp(d, ERR_TRANS_NOT_FOUND, "Tranzaksiya topilmadi")

        if txn.click_trans_id != d.get("click_trans_id"):
            return self._resp(d, ERR_TRANS_NOT_FOUND, "Tranzaksiya mos kelmadi")

        order = txn.order

        # Click o'z tomonida xatoni bildirsa (manfiy error) -> bekor qilamiz.
        try:
            click_error = int(d.get("error") or 0)
        except (ValueError, TypeError):
            click_error = 0
        if click_error < 0:
            if txn.status != ClickTransaction.Status.CONFIRMED:
                txn.status = ClickTransaction.Status.CANCELLED
                txn.save(update_fields=["status", "updated_at"])
                self._cancel_order(order)
            return self._resp(d, ERR_TRANS_CANCELLED, "Tranzaksiya bekor qilindi")

        if txn.status == ClickTransaction.Status.CONFIRMED:  # idempotent
            return self._resp(d, ERR_SUCCESS, "Success", extra={"merchant_confirm_id": txn.id})
        if txn.status == ClickTransaction.Status.CANCELLED:
            return self._resp(d, ERR_TRANS_CANCELLED, "Tranzaksiya bekor qilingan")
        if not self._amount_ok(order, d.get("amount")):
            return self._resp(d, ERR_INCORRECT_AMOUNT, "Noto'g'ri summa")

        # To'lov muvaffaqiyatli -> zakaz tayyorlanishga (oshpazga) o'tadi.
        txn.status = ClickTransaction.Status.CONFIRMED
        txn.save(update_fields=["status", "updated_at"])
        order.payment_status = Order.PaymentStatus.PAID
        order.status = Order.Status.PREPARING
        order.save(update_fields=["payment_status", "status", "updated_at"])
        return self._resp(d, ERR_SUCCESS, "Success", extra={"merchant_confirm_id": txn.id})
