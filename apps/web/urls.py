from django.urls import path

from .views import cashier, customer_menu, kitchen

urlpatterns = [
    path("t/<uuid:token>/", customer_menu, name="customer-menu"),
    path("kassir/", cashier, name="cashier"),
    path("oshpaz/", kitchen, name="kitchen"),
]
