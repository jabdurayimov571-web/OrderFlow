import uuid
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.menu.models import Category, MenuItem, Modifier
from apps.orders.models import Order
from apps.tables.models import Table

User = get_user_model()


class OrderCreateTests(APITestCase):
    """Mijoz zakaz berishi — naqd/online oqimi, summa, validatsiya."""

    def setUp(self):
        cache.clear()  # ScopedRateThrottle hisoblagichini har test uchun tozalaymiz
        self.table = Table.objects.create(number=1)
        self.cat = Category.objects.create(name="Burgerlar")
        self.item = MenuItem.objects.create(
            category=self.cat, name="Burger", price=Decimal("20000.00")
        )
        self.mod = Modifier.objects.create(
            menu_item=self.item, name="Katta", price_delta=Decimal("5000.00")
        )
        self.url = "/api/orders/"

    def _payload(self, **over):
        d = {
            "table_token": str(self.table.qr_token),
            "payment_method": "cash",
            "items": [{"menu_item": self.item.id, "quantity": 2}],
        }
        d.update(over)
        return d

    def test_create_cash_order_awaits_payment(self):
        res = self.client.post(self.url, self._payload(), format="json")
        self.assertEqual(res.status_code, 201)
        order = Order.objects.get(public_id=res.data["public_id"])
        self.assertEqual(order.status, Order.Status.AWAITING_PAYMENT)
        self.assertEqual(order.payment_method, Order.PaymentMethod.CASH)
        self.assertEqual(order.total, Decimal("40000.00"))  # 20000 * 2

    def test_create_online_order_is_created_status(self):
        res = self.client.post(self.url, self._payload(payment_method="online"), format="json")
        self.assertEqual(res.status_code, 201)
        order = Order.objects.get(public_id=res.data["public_id"])
        self.assertEqual(order.status, Order.Status.CREATED)

    def test_total_includes_modifiers(self):
        payload = self._payload(
            items=[{"menu_item": self.item.id, "quantity": 1, "modifiers": [self.mod.id]}]
        )
        res = self.client.post(self.url, payload, format="json")
        self.assertEqual(res.status_code, 201)
        order = Order.objects.get(public_id=res.data["public_id"])
        self.assertEqual(order.total, Decimal("25000.00"))  # 20000 + 5000

    def test_empty_items_rejected(self):
        res = self.client.post(self.url, self._payload(items=[]), format="json")
        self.assertEqual(res.status_code, 400)

    def test_unknown_table_token_rejected(self):
        res = self.client.post(self.url, self._payload(table_token=str(uuid.uuid4())), format="json")
        self.assertEqual(res.status_code, 400)

    def test_inactive_table_rejected(self):
        self.table.is_active = False
        self.table.save()
        res = self.client.post(self.url, self._payload(), format="json")
        self.assertEqual(res.status_code, 400)

    def test_order_number_increments_per_day(self):
        r1 = self.client.post(self.url, self._payload(), format="json")
        r2 = self.client.post(self.url, self._payload(), format="json")
        self.assertEqual(r1.data["number"], 1)
        self.assertEqual(r2.data["number"], 2)

    def test_status_retrieval_by_public_id(self):
        pid = self.client.post(self.url, self._payload(), format="json").data["public_id"]
        res = self.client.get(f"/api/orders/{pid}/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["public_id"], pid)


class StaffOrderTests(APITestCase):
    """Kassir/oshpaz oqimi va rol ruxsatlari (TokenAuth)."""

    def setUp(self):
        cache.clear()
        self.table = Table.objects.create(number=1)
        self.kassir = User.objects.create_user(
            username="kassir1", password="x", role=User.Role.KASSIR
        )
        self.oshpaz = User.objects.create_user(
            username="oshpaz1", password="x", role=User.Role.OSHPAZ
        )
        self.kassir_token = Token.objects.create(user=self.kassir)
        self.oshpaz_token = Token.objects.create(user=self.oshpaz)

    def _order(self, status, payment_method=Order.PaymentMethod.CASH):
        return Order.objects.create(
            table=self.table,
            status=status,
            payment_method=payment_method,
            total=Decimal("10000.00"),
        )

    def _auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    # --- Kassir ---
    def test_cashier_list_requires_auth(self):
        res = self.client.get("/api/orders/cashier/")
        self.assertIn(res.status_code, (401, 403))

    def test_cashier_list_forbidden_for_kitchen(self):
        self._auth(self.oshpaz_token)
        res = self.client.get("/api/orders/cashier/")
        self.assertEqual(res.status_code, 403)

    def test_cashier_list_shows_only_awaiting_payment(self):
        self._order(Order.Status.AWAITING_PAYMENT)
        self._order(Order.Status.PREPARING)
        self._auth(self.kassir_token)
        res = self.client.get("/api/orders/cashier/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)

    def test_cashier_confirm_payment_moves_to_preparing(self):
        order = self._order(Order.Status.AWAITING_PAYMENT)
        self._auth(self.kassir_token)
        res = self.client.post(f"/api/orders/cashier/{order.public_id}/confirm/")
        self.assertEqual(res.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PREPARING)
        self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)

    def test_cashier_confirm_wrong_status_404(self):
        order = self._order(Order.Status.PREPARING)
        self._auth(self.kassir_token)
        res = self.client.post(f"/api/orders/cashier/{order.public_id}/confirm/")
        self.assertEqual(res.status_code, 404)

    # --- Oshpaz ---
    def test_kitchen_list_requires_auth(self):
        res = self.client.get("/api/orders/kitchen/")
        self.assertIn(res.status_code, (401, 403))

    def test_kitchen_list_forbidden_for_cashier(self):
        self._auth(self.kassir_token)
        res = self.client.get("/api/orders/kitchen/")
        self.assertEqual(res.status_code, 403)

    def test_kitchen_list_shows_only_preparing(self):
        self._order(Order.Status.PREPARING)
        self._order(Order.Status.AWAITING_PAYMENT)
        self._auth(self.oshpaz_token)
        res = self.client.get("/api/orders/kitchen/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)

    @patch("apps.orders.views.send_order_ready_push")
    def test_kitchen_mark_ready(self, mock_push):
        order = self._order(Order.Status.PREPARING)
        self._auth(self.oshpaz_token)
        res = self.client.post(f"/api/orders/kitchen/{order.public_id}/ready/")
        self.assertEqual(res.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.READY)
        mock_push.assert_called_once()
