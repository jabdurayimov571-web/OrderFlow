from django.urls import path

from .views import customer_menu

urlpatterns = [
    path("t/<uuid:token>/", customer_menu, name="customer-menu"),
]
