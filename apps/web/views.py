import os

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render


def customer_menu(request, token):
    """Mijoz QR'ni skanerlaganda ochiladigan menyu/zakaz sahifasi."""
    return render(request, "web/menu.html", {"token": token})


def cashier(request):
    """Kassir oynasi (login + to'lov tasdiqlash)."""
    return render(request, "web/cashier.html")


def kitchen(request):
    """Oshpaz oynasi (KDS)."""
    return render(request, "web/kitchen.html")


def dashboard(request):
    """Admin boshqaruv paneli (analitika). Auth front-end tomonidan token bilan."""
    return render(request, "web/dashboard.html")


def service_worker(request):
    """Service worker'ni ildiz (/) scope bilan xizmat qiladi (Web Push uchun shart)."""
    path = os.path.join(settings.BASE_DIR, "static", "web", "sw.js")
    with open(path, "r", encoding="utf-8") as f:
        js = f.read()
    return HttpResponse(js, content_type="application/javascript")
