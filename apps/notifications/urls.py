from django.urls import path

from .views import SubscribeView, VapidKeyView

urlpatterns = [
    path("vapid-key/", VapidKeyView.as_view(), name="vapid-key"),
    path("subscribe/", SubscribeView.as_view(), name="push-subscribe"),
]
