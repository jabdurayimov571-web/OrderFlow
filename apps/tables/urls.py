from django.urls import path

from .views import TableResolveView

urlpatterns = [
    path("<uuid:token>/", TableResolveView.as_view(), name="table-resolve"),
]
