import json

from django.conf import settings
from pywebpush import WebPushException, webpush


def send_order_ready_push(order):
    """Zakaz TAYYOR bo'lganda mijozning push obunalariga xabar jo'natadi.

    Xato bo'lsa ham (tarmoq, eskirgan obuna) zakaz holatiga ta'sir qilmaydi.
    Yuborilgan obunalar sonini qaytaradi.
    """
    subs = list(order.push_subscriptions.all())
    if not subs:
        return 0

    payload = json.dumps({
        "title": "Zakaz tayyor! 🎉",
        "body": f"#{order.number} raqamli zakazingiz tayyor. Iltimos, olib keting.",
        "url": f"/t/{order.table.qr_token}/",
    })
    sent = 0
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=payload,
                vapid_private_key=str(settings.VAPID_PRIVATE_KEY_PATH),
                vapid_claims={"sub": settings.VAPID_CLAIM_EMAIL},
                timeout=10,
            )
            sent += 1
        except WebPushException as exc:
            # Obuna eskirgan/yaroqsiz (404/410) -> bazadan o'chiramiz
            if exc.response is not None and exc.response.status_code in (404, 410):
                sub.delete()
        except Exception:
            # Boshqa xatolar zakaz oqimini buzmasin
            pass
    return sent
