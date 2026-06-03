# OrderFlow 🍔

Fast-food zonalari uchun **QR orqali zakaz tizimi**. Mijoz stol ustidagi QR kodni
skanerlaydi, menyudan taom tanlaydi va zakaz beradi. Zakaz kassir va oshpazga tushadi;
tayyor bo'lganda mijozga xabar beriladi.

## Texnologiyalar

- **Backend:** Python 3.12 · Django 5.2 (LTS) · Django REST Framework
- **DB:** SQLite (dev) / PostgreSQL (prod) — `DATABASE_URL` orqali sozlanadi
- **Frontend:** Vanilla HTML / CSS / JavaScript (PWA)
- **Bildirishnoma:** Web Push + jonli status sahifa

## O'rnatish (dev)

```powershell
# 1. Virtual muhitni faollashtirish
.\venv\Scripts\Activate.ps1

# 2. Paketlar (agar kerak bo'lsa)
pip install -r requirements.txt

# 3. Env faylni tayyorlash (va SECRET_KEY ni o'zgartiring)
copy .env.example .env

# 4. Migratsiya
python manage.py migrate

# 5. Serverni ishga tushirish
python manage.py runserver
```

Sayt: http://127.0.0.1:8000

## Struktura

```
OrderFlow/
├── config/        # Django loyiha sozlamalari (settings, urls)
├── apps/          # Django ilovalar (keyingi bosqichlarda)
├── templates/     # HTML shablonlar
├── static/        # CSS, JS, rasm
├── media/         # yuklangan fayllar
└── manage.py
```

## Reja

To'liq yo'l xaritasi va qarorlar: [PLAN.md](PLAN.md)
