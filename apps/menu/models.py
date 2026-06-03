from django.db import models

from apps.common.models import TimeStampedModel


class Category(TimeStampedModel):
    """Menyu kategoriyasi (Burgerlar, Ichimliklar, ...)."""

    name = models.CharField("Nomi", max_length=100, unique=True)
    sort_order = models.PositiveIntegerField("Tartib", default=0)
    is_active = models.BooleanField("Faolmi", default=True)

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class MenuItem(TimeStampedModel):
    """Menyudagi taom."""

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Kategoriya",
    )
    name = models.CharField("Nomi", max_length=150)
    description = models.TextField("Tavsif", blank=True)
    price = models.DecimalField("Narxi", max_digits=10, decimal_places=2)
    image = models.ImageField("Rasm", upload_to="menu/", blank=True, null=True)
    is_available = models.BooleanField("Mavjudmi", default=True)
    sort_order = models.PositiveIntegerField("Tartib", default=0)

    class Meta:
        verbose_name = "Taom"
        verbose_name_plural = "Taomlar"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return f"{self.name} ({self.price})"


class Modifier(TimeStampedModel):
    """Taom uchun variant/qo'shimcha (masalan: Katta +5000, Qo'shimcha pishloq +3000)."""

    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name="modifiers",
        verbose_name="Taom",
    )
    name = models.CharField("Nomi", max_length=100)
    price_delta = models.DecimalField(
        "Narx farqi", max_digits=10, decimal_places=2, default=0
    )
    is_active = models.BooleanField("Faolmi", default=True)

    class Meta:
        verbose_name = "Variant"
        verbose_name_plural = "Variantlar"
        ordering = ["name"]

    def __str__(self):
        sign = "+" if self.price_delta >= 0 else ""
        return f"{self.name} ({sign}{self.price_delta})"
