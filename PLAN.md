# OrderFlow — Loyiha rejasi

Fast-food zonalari uchun QR orqali zakaz tizimi.

- **Boshlangan:** 2026-06-03
- **Ko'lam:** Bitta restoran (MVP)
- **Joylashuv:** `C:\Najot ta'lim\loihalarim\OrderFlow`

## Texnologiyalar

- **Backend:** Python 3.12 · Django 5.2 (LTS) · Django REST Framework
- **Ma'lumotlar bazasi:** Dev — SQLite; Prod — PostgreSQL (`DATABASE_URL` orqali)
- **Bildirishnoma:** Web Push (pywebpush, VAPID) + Service Worker (PWA)
- **Frontend:** Sof Vanilla HTML / CSS / JavaScript (PWA)
- **Rasm:** Pillow
- **Real-time:** Polling (fetch) — WebSocket/Channels ishlatilmaydi

## Rollar

- **Admin** — menyu, stollar, QR, xodimlar, analitika
- **Kassir** — tasdiqlash oynasi (naqd zakazlar, to'lovni tasdiqlash)
- **Oshpaz** — tayyorlash oynasi / KDS
- **Mijoz** — login yo'q; QR → menyu → savat → status

## Zakaz holatlari (state machine)

```
YARATILDI
   ├─ (naqd)   → KASSADA_TO'LOV_KUTILMOQDA → [kassir tasdiqlaydi] ─┐
   └─ (online) → [to'lov OK] ──────────────────────────────────────┤
                                                                    ▼
                                                            TAYYORLANMOQDA
                                                                    ▼
                                                                 TAYYOR ──► [Web Push]
                                                                    ▼
                                                                 BERILDI
   (istalgan nuqtada → BEKOR_QILINDI)
```

## To'lov oqimi

- **Naqd:** zakaz → kassir oynasida tarkib + narx ko'rinadi → mijoz kassada to'laydi
  → kassir tasdiqlaydi → tayyorlash oynasiga o'tadi.
- **Online (Payme/Click):** to'lov muvaffaqiyatli → to'g'ridan-to'g'ri tayyorlash oynasiga.

## Bildirishnoma (yagona qatlamli dizayn — naqd/online farqsiz)

1. **Jonli status sahifa + ovoz** — hamma qurilmada (iOS Safari ham)
2. **Web Push (bonus)** — Android avto; iOS faqat "Bosh ekranga qo'shish" + ruxsat bilan
3. **Pickup tablo + zakaz raqami** (ixtiyoriy) — qurilmadan mustaqil, eng ishonchli
4. **Telegram bot** (keyinroq) — iOS fonini ham 100% yopadi

## Bosqichlar (roadmap)

- [x] **0. Setup** — repo, Django+DRF, env config, skelet ✅
- [x] **1. Auth & rollar** — admin / kassir / oshpaz ✅
- [x] **2. Menyu** — kategoriya, taom, variant (modifier), rasm ✅
- [ ] **3. Stol & QR** — stol, imzolangan QR token, generatsiya/chop
- [ ] **4. Mijoz oqimi** — QR → menyu → savat → zakaz berish
- [ ] **5. Kassir oynasi** — tasdiqlash, to'lov qabul qilish
- [ ] **6. Oshpaz oynasi (KDS)** — tayyorlash, taymer, "Tayyor"
- [ ] **7. Mijoz status + Web Push** — PWA, service worker, ovoz/tebranish
- [ ] **8. Online to'lov** — Payme/Click integratsiya
- [ ] **9. Analitika** — savdo, top taomlar, o'rtacha vaqt
- [ ] **10. Sayqal** — i18n (uz/ru), PWA, xavfsizlik, deploy (HTTPS)

## Ish uslubi

Har bosqich oxirida **commit + push**. Har bosqichni **alohida tasdiqdan** keyin boshlash.
