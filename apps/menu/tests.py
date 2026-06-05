from decimal import Decimal

from rest_framework.test import APITestCase

from apps.menu.models import Category, MenuItem, Modifier


class MenuAPITests(APITestCase):
    """Mijoz menyusi API — faqat faol kategoriya va mavjud taomlar ko'rinadi."""

    def setUp(self):
        self.cat = Category.objects.create(name="Ichimliklar")
        self.item = MenuItem.objects.create(
            category=self.cat, name="Cola", price=Decimal("8000.00")
        )
        self.unavailable = MenuItem.objects.create(
            category=self.cat, name="Tugagan", price=Decimal("5000.00"), is_available=False
        )
        Modifier.objects.create(menu_item=self.item, name="Muzli", price_delta=Decimal("0"))

    def test_categories_list_ok(self):
        res = self.client.get("/api/menu/categories/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Ichimliklar", [c["name"] for c in res.data])

    def test_category_excludes_unavailable_items(self):
        res = self.client.get("/api/menu/categories/")
        cat = next(c for c in res.data if c["name"] == "Ichimliklar")
        names = [i["name"] for i in cat["items"]]
        self.assertIn("Cola", names)
        self.assertNotIn("Tugagan", names)

    def test_inactive_category_hidden(self):
        Category.objects.create(name="Yashirin", is_active=False)
        res = self.client.get("/api/menu/categories/")
        self.assertNotIn("Yashirin", [c["name"] for c in res.data])

    def test_items_list_only_available(self):
        res = self.client.get("/api/menu/items/")
        names = [i["name"] for i in res.data]
        self.assertIn("Cola", names)
        self.assertNotIn("Tugagan", names)

    def test_items_filter_by_category(self):
        other = Category.objects.create(name="Boshqa")
        MenuItem.objects.create(category=other, name="Boshqa taom", price=Decimal("1000.00"))
        res = self.client.get(f"/api/menu/items/?category={self.cat.id}")
        names = [i["name"] for i in res.data]
        self.assertIn("Cola", names)
        self.assertNotIn("Boshqa taom", names)
