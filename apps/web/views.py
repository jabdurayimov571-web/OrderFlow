from django.shortcuts import render


def customer_menu(request, token):
    """Mijoz QR'ni skanerlaganda ochiladigan menyu/zakaz sahifasi.

    Token tekshiruvi va menyu yuklash front-end (JS) tomonidan API orqali bajariladi.
    """
    return render(request, "web/menu.html", {"token": token})
