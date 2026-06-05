from django.urls import path

from .views import (
    ClickCheckoutURLView,
    ClickCompleteView,
    ClickPrepareView,
    PaymeCheckoutURLView,
    PaymeWebhookView,
)

urlpatterns = [
    # --- Payme ---
    # Payme serveri chaqiradigan JSON-RPC webhook
    path("payme/", PaymeWebhookView.as_view(), name="payme-webhook"),
    # Mijozga Payme to'lov sahifasi URL'i
    path("<uuid:public_id>/payme-url/", PaymeCheckoutURLView.as_view(), name="payme-url"),
    # --- Click ---
    # Click serveri chaqiradigan Prepare/Complete
    path("click/prepare/", ClickPrepareView.as_view(), name="click-prepare"),
    path("click/complete/", ClickCompleteView.as_view(), name="click-complete"),
    # Mijozga Click to'lov sahifasi URL'i
    path("<uuid:public_id>/click-url/", ClickCheckoutURLView.as_view(), name="click-url"),
]
