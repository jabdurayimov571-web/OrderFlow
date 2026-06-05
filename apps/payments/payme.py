"""Payme Merchant API — biznes mantiq (JSON-RPC metodlari).

Payme serveri shu metodlarni HTTP POST + JSON-RPC 2.0 orqali chaqiradi.
Summa har doim tiyinda (1 so'm = 100 tiyin). Holat mashinasi:
  1  (CREATED)   -> CreateTransaction
  2  (PERFORMED) -> PerformTransaction (zakaz PREPARING ga o'tadi)
  -1 (CANCELLED) -> yaratilgan holatda bekor
  -2 (CANCELLED_AFTER_PERFORM) -> yakunlangandan keyin bekor

Hujjat: https://developer.help.paycom.uz/metody-merchant-api/
"""

import base64
import time

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError

from apps.orders.models import Order

from .models import PaymeTransaction

# --- Xato kodlari (rasmiy protokol) ---
ERR_PARSE = -32700
ERR_INVALID_REQUEST = -32600
ERR_METHOD_NOT_FOUND = -32601
ERR_INSUFFICIENT_PRIVILEGE = -32504  # auth muvaffaqiyatsiz
ERR_SYSTEM = -32400

ERR_INVALID_AMOUNT = -31001
ERR_TRANSACTION_NOT_FOUND = -31003
ERR_CANT_CANCEL = -31007  # xizmat to'liq ko'rsatildi
ERR_CANT_PERFORM = -31008  # holat mos emas / bajarib bo'lmaydi
ERR_ACCOUNT_NOT_FOUND = -31050  # hisob (account) xatosi: -31050..-31099

# Tranzaksiyaning yakunlanishi uchun ruxsat etilgan vaqt (12 soat).
TIMEOUT_MS = 12 * 60 * 60 * 1000
REASON_TIMEOUT = 4  # Payme bekor sababi: muddat o'tdi


def _msg(uz, ru, en):
    """Payme lokalizatsiyalangan xabarni kutadi ({uz, ru, en})."""
    return {"uz": uz, "ru": ru, "en": en}


def _now_ms():
    return int(time.time() * 1000)


class PaymeError(Exception):
    """JSON-RPC error javobiga aylantiriladigan istisno."""

    def __init__(self, code, message, data=None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(str(message))


def build_payme_checkout_url(order):
    """Mijozni Payme to'lov sahifasiga yo'naltiruvchi URL (base64 parametrlar)."""
    field = settings.PAYME_ACCOUNT_FIELD
    amount_tiyin = int(order.total * 100)
    return_url = f"{settings.SITE_URL}/t/{order.table.qr_token}/"
    raw = (
        f"m={settings.PAYME_MERCHANT_ID};"
        f"ac.{field}={order.public_id};"
        f"a={amount_tiyin};"
        f"c={return_url}"
    )
    encoded = base64.b64encode(raw.encode()).decode()
    return f"{settings.PAYME_CHECKOUT_URL}/{encoded}"


class PaymeService:
    """JSON-RPC metodlarini bajaruvchi servis. Har biri dict qaytaradi yoki
    PaymeError ko'taradi. Chaqiruvchi (view) atomic tranzaksiyada ishlatadi."""

    # --- Yordamchilar ---
    def _find_order(self, account):
        field = settings.PAYME_ACCOUNT_FIELD
        value = account.get(field) if isinstance(account, dict) else None
        if not value:
            raise PaymeError(
                ERR_ACCOUNT_NOT_FOUND,
                _msg("Zakaz topilmadi", "Заказ не найден", "Order not found"),
                data=field,
            )
        try:
            return Order.objects.get(public_id=value)
        except (Order.DoesNotExist, DjangoValidationError, ValueError):
            raise PaymeError(
                ERR_ACCOUNT_NOT_FOUND,
                _msg("Zakaz topilmadi", "Заказ не найден", "Order not found"),
                data=field,
            )

    def _validate_amount(self, order, amount):
        if amount != int(order.total * 100):
            raise PaymeError(
                ERR_INVALID_AMOUNT,
                _msg("Noto'g'ri summa", "Неверная сумма", "Invalid amount"),
            )

    def _validate_payable(self, order):
        """Zakaz online to'lovga tayyor (yaratilgan, hali to'lanmagan) bo'lishi shart."""
        if (
            order.payment_method != Order.PaymentMethod.ONLINE
            or order.status != Order.Status.CREATED
        ):
            raise PaymeError(
                ERR_CANT_PERFORM,
                _msg(
                    "Zakaz holati to'lovga mos emas",
                    "Состояние заказа не позволяет оплату",
                    "Order is not payable",
                ),
            )

    def _get_txn(self, txn_id, lock=False):
        qs = PaymeTransaction.objects.all()
        if lock:
            qs = qs.select_for_update()
        txn = qs.filter(transaction_id=txn_id).first()
        if not txn:
            raise PaymeError(
                ERR_TRANSACTION_NOT_FOUND,
                _msg("Tranzaksiya topilmadi", "Транзакция не найдена", "Transaction not found"),
            )
        return txn

    def _cancel_order(self, order, refund=False):
        order.status = Order.Status.CANCELLED
        if refund:
            order.payment_status = Order.PaymentStatus.UNPAID
        order.save(update_fields=["status", "payment_status", "updated_at"])

    # --- JSON-RPC metodlari ---
    def check_perform_transaction(self, params):
        order = self._find_order(params.get("account") or {})
        self._validate_amount(order, params.get("amount"))
        self._validate_payable(order)
        return {"allow": True}

    def create_transaction(self, params):
        txn_id = params.get("id")
        existing = self._get_txn_or_none(txn_id)
        if existing:
            if existing.state != PaymeTransaction.STATE_CREATED:
                raise PaymeError(
                    ERR_CANT_PERFORM,
                    _msg("Tranzaksiya holati mos emas", "Состояние транзакции неверно", "Invalid state"),
                )
            return {
                "create_time": existing.create_time,
                "transaction": str(existing.id),
                "state": existing.state,
            }

        order = self._find_order(params.get("account") or {})
        self._validate_amount(order, params.get("amount"))
        self._validate_payable(order)
        # Bitta zakazga bir vaqtning o'zida faqat bitta faol tranzaksiya.
        if order.payme_transactions.filter(
            state__in=[PaymeTransaction.STATE_CREATED, PaymeTransaction.STATE_PERFORMED]
        ).exists():
            raise PaymeError(
                ERR_CANT_PERFORM,
                _msg(
                    "Zakaz allaqachon to'lov jarayonida",
                    "Заказ уже в процессе оплаты",
                    "Order is already being paid",
                ),
            )
        txn = PaymeTransaction.objects.create(
            order=order,
            transaction_id=txn_id,
            amount=int(params["amount"]),
            state=PaymeTransaction.STATE_CREATED,
            create_time=params.get("time") or _now_ms(),
        )
        return {
            "create_time": txn.create_time,
            "transaction": str(txn.id),
            "state": txn.state,
        }

    def perform_transaction(self, params):
        txn = self._get_txn(params.get("id"), lock=True)
        if txn.state == PaymeTransaction.STATE_CREATED:
            if (_now_ms() - txn.create_time) > TIMEOUT_MS:
                txn.state = PaymeTransaction.STATE_CANCELLED
                txn.reason = REASON_TIMEOUT
                txn.cancel_time = _now_ms()
                txn.save(update_fields=["state", "reason", "cancel_time", "updated_at"])
                self._cancel_order(txn.order)
                raise PaymeError(
                    ERR_CANT_PERFORM,
                    _msg("Tranzaksiya muddati o'tdi", "Срок транзакции истёк", "Transaction expired"),
                )
            txn.state = PaymeTransaction.STATE_PERFORMED
            txn.perform_time = _now_ms()
            txn.save(update_fields=["state", "perform_time", "updated_at"])
            # To'lov muvaffaqiyatli -> zakaz tayyorlanishga (oshpazga) o'tadi.
            order = txn.order
            order.payment_status = Order.PaymentStatus.PAID
            order.status = Order.Status.PREPARING
            order.save(update_fields=["payment_status", "status", "updated_at"])
            return {
                "transaction": str(txn.id),
                "perform_time": txn.perform_time,
                "state": txn.state,
            }
        if txn.state == PaymeTransaction.STATE_PERFORMED:
            return {
                "transaction": str(txn.id),
                "perform_time": txn.perform_time,
                "state": txn.state,
            }
        raise PaymeError(
            ERR_CANT_PERFORM,
            _msg("Tranzaksiyani bajarib bo'lmaydi", "Невозможно выполнить", "Cannot perform"),
        )

    def cancel_transaction(self, params):
        txn = self._get_txn(params.get("id"), lock=True)
        reason = params.get("reason")
        if txn.state == PaymeTransaction.STATE_CREATED:
            txn.state = PaymeTransaction.STATE_CANCELLED
            txn.cancel_time = _now_ms()
            txn.reason = reason
            txn.save(update_fields=["state", "cancel_time", "reason", "updated_at"])
            self._cancel_order(txn.order)
        elif txn.state == PaymeTransaction.STATE_PERFORMED:
            order = txn.order
            # Xizmat to'liq ko'rsatilgan bo'lsa (tayyor/berildi) bekor qilib bo'lmaydi.
            if order.status in (Order.Status.READY, Order.Status.COMPLETED):
                raise PaymeError(
                    ERR_CANT_CANCEL,
                    _msg(
                        "Xizmat ko'rsatildi, bekor qilib bo'lmaydi",
                        "Услуга оказана, отмена невозможна",
                        "Service delivered, cannot cancel",
                    ),
                )
            txn.state = PaymeTransaction.STATE_CANCELLED_AFTER_PERFORM
            txn.cancel_time = _now_ms()
            txn.reason = reason
            txn.save(update_fields=["state", "cancel_time", "reason", "updated_at"])
            self._cancel_order(order, refund=True)
        # Allaqachon bekor qilingan (-1/-2): idempotent, holatni qaytaramiz.
        return {
            "transaction": str(txn.id),
            "cancel_time": txn.cancel_time,
            "state": txn.state,
        }

    def check_transaction(self, params):
        txn = self._get_txn(params.get("id"))
        return {
            "create_time": txn.create_time,
            "perform_time": txn.perform_time,
            "cancel_time": txn.cancel_time,
            "transaction": str(txn.id),
            "state": txn.state,
            "reason": txn.reason,
        }

    def get_statement(self, params):
        frm = params.get("from", 0)
        to = params.get("to", _now_ms())
        field = settings.PAYME_ACCOUNT_FIELD
        txns = PaymeTransaction.objects.filter(
            create_time__gte=frm, create_time__lte=to
        ).select_related("order").order_by("create_time")
        return {
            "transactions": [
                {
                    "id": t.transaction_id,
                    "time": t.create_time,
                    "amount": t.amount,
                    "account": {field: str(t.order.public_id)},
                    "create_time": t.create_time,
                    "perform_time": t.perform_time,
                    "cancel_time": t.cancel_time,
                    "transaction": str(t.id),
                    "state": t.state,
                    "reason": t.reason,
                }
                for t in txns
            ]
        }

    def _get_txn_or_none(self, txn_id):
        return PaymeTransaction.objects.filter(transaction_id=txn_id).first()
