from django.db import models

from apps.common.models import TimeStampedModel


class PushSubscription(TimeStampedModel):
    """Mijozning Web Push obunasi (zakazga bog'langan)."""

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="push_subscriptions",
        verbose_name="Zakaz",
    )
    endpoint = models.TextField("Endpoint")
    p256dh = models.CharField("p256dh kalit", max_length=255)
    auth = models.CharField("auth kalit", max_length=255)

    class Meta:
        verbose_name = "Push obuna"
        verbose_name_plural = "Push obunalar"

    def __str__(self):
        return f"Push obuna (zakaz #{self.order.number})"
