from django.urls import path

from .views import (
    CashierConfirmPaymentView,
    CashierOrderListView,
    OrderCreateView,
    OrderStatusView,
)

urlpatterns = [
    path("", OrderCreateView.as_view(), name="order-create"),
    path("cashier/", CashierOrderListView.as_view(), name="cashier-orders"),
    path("cashier/<int:pk>/confirm/", CashierConfirmPaymentView.as_view(), name="cashier-confirm"),
    path("<uuid:public_id>/", OrderStatusView.as_view(), name="order-status"),
]
