from django.urls import path

from .views import (
    CashierConfirmPaymentView,
    CashierOrderListView,
    KitchenMarkReadyView,
    KitchenOrderListView,
    OrderCreateView,
    OrderStatusView,
)

urlpatterns = [
    path("", OrderCreateView.as_view(), name="order-create"),
    path("cashier/", CashierOrderListView.as_view(), name="cashier-orders"),
    path("cashier/<uuid:public_id>/confirm/", CashierConfirmPaymentView.as_view(), name="cashier-confirm"),
    path("kitchen/", KitchenOrderListView.as_view(), name="kitchen-orders"),
    path("kitchen/<uuid:public_id>/ready/", KitchenMarkReadyView.as_view(), name="kitchen-ready"),
    path("<uuid:public_id>/", OrderStatusView.as_view(), name="order-status"),
]
