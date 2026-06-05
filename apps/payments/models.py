"""To'lov tranzaksiyalari — Payme (Merchant API) va Click (SHOP API).

Har bir provayder o'z protokoliga ega, shuning uchun alohida modellar:
- Payme: butun sonli holatlar (1/2/-1/-2) va ms-timestamp'lar bilan ishlaydi,
  summa tiyinda (1 so'm = 100 tiyin).
- Click: Prepare/Complete bosqichlari va so'mdagi summa bilan ishlaydi.

Tranzaksiya yozuvlari moliyaviy ahamiyatga ega, shuning uchun bog'liq zakaz
PROTECT bilan himoyalanadi (tranzaksiyasi bor zakazni o'chirib bo'lmaydi).
"""

from django.db import models

from apps.common.models import TimeStampedModel


class PaymeTransaction(TimeStampedModel):
    """Payme Merchant API tranzaksiyasi (CreateTransaction da yaratiladi)."""

    # Payme holat kodlari (rasmiy protokol)
    STATE_CREATED = 1  # yaratildi, PerformTransaction kutilmoqda
    STATE_PERFORMED = 2  # muvaffaqiyatli yakunlandi
    STATE_CANCELLED = -1  # yaratilgan holatda bekor qilindi
    STATE_CANCELLED_AFTER_PERFORM = -2  # yakunlangandan keyin bekor qilindi

    STATE_CHOICES = [
        (STATE_CREATED, "Yaratildi"),
        (STATE_PERFORMED, "Yakunlandi"),
        (STATE_CANCELLED, "Bekor (yaratilgan)"),
        (STATE_CANCELLED_AFTER_PERFORM, "Bekor (yakunlangan)"),
    ]

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="payme_transactions",
        verbose_name="Zakaz",
    )
    transaction_id = models.CharField(
        "Payme tranzaksiya ID", max_length=64, unique=True
    )
    amount = models.BigIntegerField("Summa (tiyin)")
    state = models.IntegerField("Holat", choices=STATE_CHOICES, default=STATE_CREATED)
    reason = models.IntegerField("Bekor sababi", null=True, blank=True)
    create_time = models.BigIntegerField("Yaratilgan vaqt (ms)", default=0)
    perform_time = models.BigIntegerField("Yakunlangan vaqt (ms)", default=0)
    cancel_time = models.BigIntegerField("Bekor vaqti (ms)", default=0)

    class Meta:
        verbose_name = "Payme tranzaksiyasi"
        verbose_name_plural = "Payme tranzaksiyalari"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payme {self.transaction_id} ({self.get_state_display()})"

    @property
    def amount_som(self):
        """Summani so'mda qaytaradi (admin/ko'rinish uchun)."""
        return self.amount / 100


class ClickTransaction(TimeStampedModel):
    """Click SHOP API tranzaksiyasi (Prepare da yaratiladi, Complete da yakunlanadi).

    Prepare javobida `merchant_prepare_id` sifatida shu yozuvning PK qaytariladi;
    Complete so'rovida Click o'sha PK ni qaytaradi va biz mosligini tekshiramiz.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Kutilmoqda"
        PREPARED = "prepared", "Tayyorlandi"
        CONFIRMED = "confirmed", "Tasdiqlandi"
        CANCELLED = "cancelled", "Bekor qilindi"

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="click_transactions",
        verbose_name="Zakaz",
    )
    click_trans_id = models.CharField(
        "Click tranzaksiya ID", max_length=64, db_index=True
    )
    click_paydoc_id = models.CharField("Click hujjat ID", max_length=64, blank=True)
    amount = models.DecimalField("Summa (so'm)", max_digits=12, decimal_places=2)
    status = models.CharField(
        "Holat", max_length=12, choices=Status.choices, default=Status.PENDING
    )

    class Meta:
        verbose_name = "Click tranzaksiyasi"
        verbose_name_plural = "Click tranzaksiyalari"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Click {self.click_trans_id} ({self.get_status_display()})"
