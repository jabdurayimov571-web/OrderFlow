from rest_framework.generics import RetrieveAPIView

from .models import Table
from .serializers import TableSerializer


class TableResolveView(RetrieveAPIView):
    """QR token orqali stolni aniqlaydi (mijoz ilovasi uchun)."""

    queryset = Table.objects.filter(is_active=True)
    serializer_class = TableSerializer
    lookup_field = "qr_token"
    lookup_url_kwarg = "token"
