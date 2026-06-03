"""OrderFlow — asosiy URL konfiguratsiyasi."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(request):
    """Oddiy health-check — server ishlayotganini tekshirish uchun."""
    return JsonResponse({"status": "ok", "service": "OrderFlow API"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", health, name="health"),
    path("api/menu/", include("apps.menu.urls")),
    path("api/tables/", include("apps.tables.urls")),
    path("api/orders/", include("apps.orders.urls")),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/push/", include("apps.notifications.urls")),
    path("", include("apps.web.urls")),
]

# Dev rejimida media fayllarni xizmat qilish
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
