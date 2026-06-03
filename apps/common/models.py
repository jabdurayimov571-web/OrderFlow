from django.db import models


class TimeStampedModel(models.Model):
    """Yaratilgan/yangilangan vaqtni avtomatik saqlovchi abstrakt model.

    Boshqa modellar shundan meros oladi (Category, MenuItem, Order, ...).
    """

    created_at = models.DateTimeField("Yaratilgan", auto_now_add=True)
    updated_at = models.DateTimeField("Yangilangan", auto_now=True)

    class Meta:
        abstract = True
