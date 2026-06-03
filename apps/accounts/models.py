from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """OrderFlow foydalanuvchisi — rol asosida ishlaydi (admin / kassir / oshpaz)."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Administrator"
        KASSIR = "kassir", "Kassir"
        OSHPAZ = "oshpaz", "Oshpaz"

    role = models.CharField(
        "Rol",
        max_length=20,
        choices=Role.choices,
        default=Role.ADMIN,
    )

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_kassir(self):
        """Foydalanuvchi kassirmi?"""
        return self.role == self.Role.KASSIR

    @property
    def is_oshpaz(self):
        """Foydalanuvchi oshpazmi?"""
        return self.role == self.Role.OSHPAZ
