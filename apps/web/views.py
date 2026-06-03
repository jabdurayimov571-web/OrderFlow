from django.shortcuts import render


def customer_menu(request, token):
    """Mijoz QR'ni skanerlaganda ochiladigan menyu/zakaz sahifasi.

    Token tekshiruvi va menyu yuklash front-end (JS) tomonidan API orqali bajariladi.
    """
    return render(request, "web/menu.html", {"token": token})


def cashier(request):
    """Kassir oynasi (login + to'lov tasdiqlash). Auth front-end tomonidan token bilan."""
    return render(request, "web/cashier.html")


def kitchen(request):
    """Oshpaz oynasi (KDS). Auth front-end tomonidan token bilan."""
    return render(request, "web/kitchen.html")
