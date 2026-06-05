import base64
import json
import time
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse

from apps.orders.models import Order
from apps.tables.models import Table

from .models import PaymeTransaction


def _auth(key="test_key"):
    return "Basic " + base64.b64encode(f"Paycom:{key}".encode()).decode()


@override_settings(
    PAYME_MERCHANT_KEY="test_key",
    PAYME_MERCHANT_ID="test_merchant",
    PAYME_ACCOUNT_FIELD="order_id",
    PAYME_CHECKOUT_URL="https://checkout.test.paycom.uz",
    SITE_URL="https://orderflow.test",
)
class PaymeWebhookTests(TestCase):
    def setUp(self):
        self.table = Table.objects.create(number=1)
        self.order = Order.objects.create(
            table=self.table,
            payment_method=Order.PaymentMethod.ONLINE,
            status=Order.Status.CREATED,
            total=Decimal("25000.00"),
        )
        self.amount = 2_500_000  # tiyin
        self.now_ms = int(time.time() * 1000)  # real (hozirgi) Payme timestamp
        self.url = reverse("payme-webhook")

    def _rpc(self, method, params, req_id=1, key="test_key"):
        resp = self.client.post(
            self.url,
            data=json.dumps(
                {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
            ),
            content_type="application/json",
            HTTP_AUTHORIZATION=_auth(key),
        )
        self.assertEqual(resp.status_code, 200)
        return resp.json()

    def _account(self):
        return {"order_id": str(self.order.public_id)}

    # --- Auth ---
    def test_auth_required(self):
        resp = self.client.post(
            self.url,
            data=json.dumps(
                {"jsonrpc": "2.0", "id": 1, "method": "CheckPerformTransaction", "params": {}}
            ),
            content_type="application/json",
        )
        self.assertEqual(resp.json()["error"]["code"], -32504)

    def test_wrong_key_rejected(self):
        body = self._rpc(
            "CheckPerformTransaction",
            {"amount": self.amount, "account": self._account()},
            key="wrong",
        )
        self.assertEqual(body["error"]["code"], -32504)

    # --- CheckPerformTransaction ---
    def test_check_perform_ok(self):
        body = self._rpc(
            "CheckPerformTransaction", {"amount": self.amount, "account": self._account()}
        )
        self.assertTrue(body["result"]["allow"])

    def test_check_perform_wrong_amount(self):
        body = self._rpc(
            "CheckPerformTransaction", {"amount": 999, "account": self._account()}
        )
        self.assertEqual(body["error"]["code"], -31001)

    def test_check_perform_order_not_found(self):
        body = self._rpc(
            "CheckPerformTransaction",
            {"amount": self.amount, "account": {"order_id": "nope"}},
        )
        self.assertEqual(body["error"]["code"], -31050)
        self.assertEqual(body["error"]["data"], "order_id")

    def test_check_perform_not_payable(self):
        cash = Order.objects.create(
            table=self.table,
            payment_method=Order.PaymentMethod.CASH,
            status=Order.Status.CREATED,
            total=Decimal("25000.00"),
        )
        body = self._rpc(
            "CheckPerformTransaction",
            {"amount": self.amount, "account": {"order_id": str(cash.public_id)}},
        )
        self.assertEqual(body["error"]["code"], -31008)

    # --- CreateTransaction ---
    def test_create_transaction(self):
        body = self._rpc(
            "CreateTransaction",
            {"id": "tx1", "time": self.now_ms, "amount": self.amount, "account": self._account()},
        )
        self.assertEqual(body["result"]["state"], 1)
        self.assertEqual(body["result"]["create_time"], self.now_ms)
        self.assertTrue(PaymeTransaction.objects.filter(transaction_id="tx1").exists())

    def test_create_transaction_idempotent(self):
        params = {
            "id": "tx1",
            "time": self.now_ms,
            "amount": self.amount,
            "account": self._account(),
        }
        b1 = self._rpc("CreateTransaction", params)
        b2 = self._rpc("CreateTransaction", params)
        self.assertEqual(b1["result"]["transaction"], b2["result"]["transaction"])
        self.assertEqual(PaymeTransaction.objects.filter(transaction_id="tx1").count(), 1)

    def test_create_second_transaction_blocked(self):
        self._rpc(
            "CreateTransaction",
            {"id": "tx1", "time": self.now_ms, "amount": self.amount, "account": self._account()},
        )
        body = self._rpc(
            "CreateTransaction",
            {"id": "tx2", "time": self.now_ms + 1, "amount": self.amount, "account": self._account()},
        )
        self.assertEqual(body["error"]["code"], -31008)

    # --- PerformTransaction ---
    def test_perform_transaction_moves_order_to_preparing(self):
        self._rpc(
            "CreateTransaction",
            {"id": "tx1", "time": self.now_ms, "amount": self.amount, "account": self._account()},
        )
        body = self._rpc("PerformTransaction", {"id": "tx1"})
        self.assertEqual(body["result"]["state"], 2)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PREPARING)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)

    def test_perform_idempotent(self):
        self._rpc(
            "CreateTransaction",
            {"id": "tx1", "time": self.now_ms, "amount": self.amount, "account": self._account()},
        )
        b1 = self._rpc("PerformTransaction", {"id": "tx1"})
        b2 = self._rpc("PerformTransaction", {"id": "tx1"})
        self.assertEqual(b1["result"]["perform_time"], b2["result"]["perform_time"])

    def test_perform_unknown_transaction(self):
        body = self._rpc("PerformTransaction", {"id": "nope"})
        self.assertEqual(body["error"]["code"], -31003)

    # --- CancelTransaction ---
    def test_cancel_created_transaction_cancels_order(self):
        self._rpc(
            "CreateTransaction",
            {"id": "tx1", "time": self.now_ms, "amount": self.amount, "account": self._account()},
        )
        body = self._rpc("CancelTransaction", {"id": "tx1", "reason": 1})
        self.assertEqual(body["result"]["state"], -1)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CANCELLED)

    # --- CheckTransaction ---
    def test_check_transaction(self):
        self._rpc(
            "CreateTransaction",
            {"id": "tx1", "time": self.now_ms, "amount": self.amount, "account": self._account()},
        )
        body = self._rpc("CheckTransaction", {"id": "tx1"})
        self.assertEqual(body["result"]["state"], 1)

    # --- Noma'lum metod ---
    def test_unknown_method(self):
        body = self._rpc("FooBar", {})
        self.assertEqual(body["error"]["code"], -32601)


@override_settings(
    PAYME_MERCHANT_ID="test_merchant",
    PAYME_ACCOUNT_FIELD="order_id",
    PAYME_CHECKOUT_URL="https://checkout.test.paycom.uz",
    SITE_URL="https://orderflow.test",
)
class PaymeCheckoutURLTests(TestCase):
    def test_checkout_url_returned(self):
        table = Table.objects.create(number=5)
        order = Order.objects.create(
            table=table,
            payment_method=Order.PaymentMethod.ONLINE,
            status=Order.Status.CREATED,
            total=Decimal("12000.00"),
        )
        url = reverse("payme-url", args=[order.public_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("checkout.test.paycom.uz", resp.json()["url"])

    def test_checkout_url_rejects_cash_order(self):
        table = Table.objects.create(number=6)
        cash = Order.objects.create(
            table=table,
            payment_method=Order.PaymentMethod.CASH,
            status=Order.Status.AWAITING_PAYMENT,
            total=Decimal("12000.00"),
        )
        url = reverse("payme-url", args=[cash.public_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 400)
