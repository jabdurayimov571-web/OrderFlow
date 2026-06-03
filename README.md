# OrderFlow 🍔

> Fast-food zonalari uchun **QR orqali zakaz tizimi**. Mijoz stol ustidagi QR kodni
> skanerlaydi, telefonidan menyuni ko'radi, zakaz beradi; zakaz kassir va oshpazga
> real vaqtda tushadi; tayyor bo'lganda mijozga xabar beriladi.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-5.2_LTS-green)
![DRF](https://img.shields.io/badge/DRF-3.17-red)
![Frontend](https://img.shields.io/badge/Frontend-Vanilla_JS-yellow)

---

## ✨ Asosiy imkoniyatlar

- 📱 **QR → menyu → savat → zakaz** — mijoz uchun ilovasiz, mobil-birinchi sahifa
- 💳 **Kassir oynasi** — naqd zakazlar (tarkib + narx), to'lovni tasdiqlash
- 🍳 **Oshpaz oynasi (KDS)** — dark-mode, jonli taymer, "Tayyor" tugmasi
- 🔔 **Bildirishnoma** — jonli status + ovoz + tebranish, hamda **Web Push (PWA)**
- 📊 **Admin paneli** — savdo, top taomlar, oxirgi 7 kun analitikasi
- 🔐 **Rollar** — admin / kassir / oshpaz; token-asosli auth, rol himoyasi
- 🛡️ **Production xavfsizlik** — HTTPS/cookie/HSTS, zakaz throttling

## 🛠 Texnologiyalar

| Qatlam | Tanlov |
|--------|--------|
| Backend | Python 3.12 · Django 5.2 (LTS) · Django REST Framework |
| Ma'lumotlar bazasi | SQLite (dev) · PostgreSQL (prod) — `DATABASE_URL` orqali |
| Frontend | Sof Vanilla HTML / CSS / JavaScript (PWA) |
| Real-time | Polling (fetch) — sodda va ishonchli |
| Bildirishnoma | Web Push (`pywebpush`, VAPID) + Service Worker |
| QR | `qrcode` |

## 🧩 Arxitektura (Django ilovalar)

```
config/            # sozlamalar, asosiy urls
apps/
├── common/        # TimeStampedModel (abstrakt baza)
├── accounts/      # custom User (rollar), token login, permissionlar
├── menu/          # Category, MenuItem, Modifier + API
├── tables/        # Table (UUID QR token), QR generatsiya
├── orders/        # Order, OrderItem, holat mashinasi, kassir/oshpaz API
├── notifications/ # PushSubscription, Web Push servisi
├── analytics/     # admin analitika API
└── web/           # mijoz/kassir/oshpaz/admin HTML sahifalari
```

**Oqim:**
```
📱 Mijoz (QR) → menyu → savat → zakaz
      ↓
💳 Kassir to'lovni tasdiqlaydi (naqd)   ──┐  online to'lov → to'g'ridan-to'g'ri
      ↓                                    ▼
🍳 Oshpaz (KDS) tayyorlaydi → "Tayyor"
      ↓
🔔 Mijozga jonli status + Web Push
```

## 👥 Rollar va sahifalar

| Sahifa | Manzil | Kim uchun |
|--------|--------|-----------|
| Mijoz menyusi | `/t/<qr_token>/` | Mijoz (loginsiz) |
| Kassir | `/kassir/` | Kassir / admin |
| Oshpaz (KDS) | `/oshpaz/` | Oshpaz / admin |
| Boshqaruv | `/boshqaruv/` | Admin |
| Django admin | `/admin/` | Admin |

## 🚀 O'rnatish (dev)

```powershell
# 1. Repo
git clone https://github.com/jabdurayimov571-web/OrderFlow.git
cd OrderFlow

# 2. Virtual muhit
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Paketlar
pip install -r requirements.txt

# 4. Env
copy .env.example .env
#   SECRET_KEY ni to'ldiring (python -c "import secrets;print(secrets.token_urlsafe(64))")

# 5. VAPID kalitlar (Web Push uchun) — qisqa skript bilan generatsiya qilinadi
#   (vapid_private.pem + .env'ga VAPID_PUBLIC_KEY)

# 6. Migratsiya + superuser
python manage.py migrate
python manage.py createsuperuser

# 7. Ishga tushirish
python manage.py runserver
```

So'ng: http://127.0.0.1:8000/admin/ (menyu, stol qo'shish) → stol QR'ini oching.

## 🔌 API (asosiy)

| Metod | Endpoint | Tavsif |
|-------|----------|--------|
| GET | `/api/menu/categories/` | Menyu (kategoriya → taom → variant) |
| GET | `/api/tables/<uuid>/` | Stolni QR token orqali aniqlash |
| POST | `/api/orders/` | Zakaz berish (savat) |
| GET | `/api/orders/<public_id>/` | Zakaz holati (mijoz) |
| POST | `/api/auth/login/` | Staff login (token) |
| GET/POST | `/api/orders/cashier/` · `.../confirm/` | Kassir: ro'yxat / to'lov tasdiq |
| GET/POST | `/api/orders/kitchen/` · `.../ready/` | Oshpaz: ro'yxat / Tayyor |
| GET | `/api/analytics/summary/` | Admin analitika |
| GET/POST | `/api/push/vapid-key/` · `/api/push/subscribe/` | Web Push |

## 🔄 Zakaz holatlari

```
YARATILDI ─(naqd)→ KASSADA_TO'LOV_KUTILMOQDA ─(kassir)→ TAYYORLANMOQDA ─(oshpaz)→ TAYYOR → BERILDI
          └(online)→ [to'lov OK] ─────────────────────────┘                 (→ BEKOR_QILINDI)
```

## 🔔 Bildirishnoma dizayni (yagona, qatlamli)

1. **Jonli status + ovoz + tebranish** — hamma qurilmada (iOS Safari ham), o'rnatishsiz
2. **Web Push (PWA)** — fon xabari (Android avto; iOS — "Bosh ekranga qo'shish")
3. *(reja)* Pickup tablo, Telegram bot

## 🧪 Test foydalanuvchilar (dev)

| Rol | Login | Parol |
|-----|-------|-------|
| Admin | `admin` | `admin12345` |
| Kassir | `kassir` | `kassir123` |
| Oshpaz | `oshpaz` | `oshpaz123` |

> ⚠️ Bu faqat dev uchun — production'da albatta o'zgartiring.

## 🌐 Production / Deploy

1. **Env:** `DEBUG=False`, kuchli `SECRET_KEY`, to'g'ri `ALLOWED_HOSTS`, `DATABASE_URL` (PostgreSQL), `SITE_URL=https://...`, `CSRF_TRUSTED_ORIGINS=https://...`
2. **DB:** PostgreSQL (`psycopg` allaqachon o'rnatilgan)
3. **Statik:** `python manage.py collectstatic`
4. **Server:** Gunicorn (WSGI) + Nginx (reverse proxy)
5. **HTTPS:** Let's Encrypt (Web Push va Service Worker uchun **shart**)
6. **VAPID:** production uchun yangi kalitlar generatsiya qiling
7. `DEBUG=False` da xavfsizlik (HSTS, secure cookie, SSL redirect) avtomatik yoqiladi — `python manage.py check --deploy` bilan tasdiqlangan

## 📄 Reja

To'liq yo'l xaritasi: [PLAN.md](PLAN.md)
