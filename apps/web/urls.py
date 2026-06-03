from django.urls import path

from .views import cashier, customer_menu, dashboard, kitchen, service_worker

urlpatterns = [
    path("t/<uuid:token>/", customer_menu, name="customer-menu"),
    path("kassir/", cashier, name="cashier"),
    path("oshpaz/", kitchen, name="kitchen"),
    path("boshqaruv/", dashboard, name="dashboard"),
    path("sw.js", service_worker, name="service-worker"),
]
