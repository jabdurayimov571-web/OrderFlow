from django.urls import path

from .views import PaymeCheckoutURLView, PaymeWebhookView

urlpatterns = [
    # Payme serveri chaqiradigan JSON-RPC webhook
    path("payme/", PaymeWebhookView.as_view(), name="payme-webhook"),
    # Mijozga to'lov sahifasi URL'i
    path("<uuid:public_id>/payme-url/", PaymeCheckoutURLView.as_view(), name="payme-url"),
]
