from django.urls import path

from .views import OrderCreateView, OrderStatusView

urlpatterns = [
    path("", OrderCreateView.as_view(), name="order-create"),
    path("<uuid:public_id>/", OrderStatusView.as_view(), name="order-status"),
]
