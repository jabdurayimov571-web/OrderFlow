import base64
import io
import uuid

import qrcode
from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class Table(TimeStampedModel):
    """Restorandagi stol — har biriga noyob QR token biriktiriladi."""

    number = models.PositiveIntegerField("Stol raqami", unique=True)
    qr_token = models.UUIDField(
        "QR token", default=uuid.uuid4, unique=True, editable=False
    )
    is_active = models.BooleanField("Faolmi", default=True)

    class Meta:
        verbose_name = "Stol"
        verbose_name_plural = "Stollar"
        ordering = ["number"]

    def __str__(self):
        return f"Stol #{self.number}"

    @property
    def menu_url(self):
        """Mijoz QR'ni skanerlaganda ochiladigan URL."""
        return f"{settings.SITE_URL}/t/{self.qr_token}/"

    def qr_png_base64(self):
        """QR kodni base64 PNG sifatida qaytaradi (admin'da ko'rsatish/chop uchun)."""
        img = qrcode.make(self.menu_url)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
