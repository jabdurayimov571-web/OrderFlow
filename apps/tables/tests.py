import uuid

from rest_framework.test import APITestCase

from apps.tables.models import Table


class TableResolveTests(APITestCase):
    """QR token orqali stolni aniqlash (faqat faol stollar)."""

    def test_resolve_active_table(self):
        table = Table.objects.create(number=7)
        res = self.client.get(f"/api/tables/{table.qr_token}/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["number"], 7)

    def test_inactive_table_404(self):
        table = Table.objects.create(number=8, is_active=False)
        res = self.client.get(f"/api/tables/{table.qr_token}/")
        self.assertEqual(res.status_code, 404)

    def test_unknown_token_404(self):
        res = self.client.get(f"/api/tables/{uuid.uuid4()}/")
        self.assertEqual(res.status_code, 404)


class TableModelTests(APITestCase):
    def test_menu_url_uses_qr_token(self):
        table = Table.objects.create(number=9)
        self.assertIn(str(table.qr_token), table.menu_url)
        self.assertTrue(table.menu_url.endswith(f"/t/{table.qr_token}/"))
