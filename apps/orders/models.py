import uuid

from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel


class Order(TimeStampedModel):
    """Mijoz zakazi — holat mashinasi orqali boshqariladi."""

    class Status(models.TextChoices):
        CREATED = "created", "Yaratildi"
        AWAITING_PAYMENT = "awaiting_payment", "Kassada to'lov kutilmoqda"
        PREPARING = "preparing", "Tayyorlanmoqda"
        READY = "ready", "Tayyor"
        COMPLETED = "completed", "Berildi"
        CANCELLED = "cancelled", "Bekor qilindi"

    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Naqd"
        ONLINE = "online", "Online"

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "To'lanmagan"
        PAID = "paid", "To'langan"

    # Mijoz holatni tekshirishi uchun taxmin qilib bo'lmaydigan ID
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    table = models.ForeignKey(
        "tables.Table",
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="Stol",
    )
    number = models.PositiveIntegerField("Zakaz raqami", default=0)
    status = models.CharField(
        "Holat", max_length=20, choices=Status.choices, default=Status.CREATED
    )
    payment_method = models.CharField(
        "To'lov turi",
        max_length=10,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
    )
    payment_status = models.CharField(
        "To'lov holati",
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
    )
    customer_note = models.TextField("Mijoz izohi", blank=True)
    total = models.DecimalField("Jami", max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Zakaz"
        verbose_name_plural = "Zakazlar"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Zakaz #{self.number}"

    def save(self, *args, **kwargs):
        # Zakaz raqamini har kun uchun ketma-ket beramiz (#1, #2, ...).
        # localdate() — mahalliy (TIME_ZONE) sana; created_at__date lookup ham
        # mahalliy vaqtda hisoblanadi, shuning uchun ular mos kelishi shart
        # (aks holda UTC-mahalliy farqi tunda hisoblagichni buzadi).
        if not self.number:
            today = timezone.localdate()
            last = Order.objects.filter(created_at__date=today).aggregate(
                m=models.Max("number")
            )["m"]
            self.number = (last or 0) + 1
        super().save(*args, **kwargs)


class OrderItem(TimeStampedModel):
    """Zakaz tarkibidagi bitta taom (narx/nom snapshot bilan saqlanadi)."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items", verbose_name="Zakaz"
    )
    menu_item = models.ForeignKey(
        "menu.MenuItem", on_delete=models.PROTECT, verbose_name="Taom"
    )
    name = models.CharField("Nomi (snapshot)", max_length=150)
    unit_price = models.DecimalField("Narx (snapshot)", max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField("Soni", default=1)
    modifiers = models.ManyToManyField(
        "menu.Modifier", blank=True, verbose_name="Variantlar"
    )
    line_total = models.DecimalField(
        "Jami (snapshot)", max_digits=10, decimal_places=2, default=0
    )
    note = models.CharField("Izoh", max_length=255, blank=True)

    class Meta:
        verbose_name = "Zakaz tarkibi"
        verbose_name_plural = "Zakaz tarkibi"

    def __str__(self):
        return f"{self.name} x{self.quantity}"
