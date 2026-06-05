"""
OrderFlow — Django 5.2 (LTS) sozlamalari.
Env-asosli konfiguratsiya (django-environ): barcha sirlar .env faylida.
"""

from pathlib import Path

import environ

# --- Asosiy yo'llar ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Environment (.env) ---
env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

# --- Xavfsizlik ---
SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# --- Ilovalar ---
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework.authtoken",
]

# Bizning ilovalar
LOCAL_APPS = [
    "apps.accounts",
    "apps.common",
    "apps.menu",
    "apps.tables",
    "apps.orders",
    "apps.payments",
    "apps.web",
    "apps.notifications",
    "apps.analytics",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Custom User modeli (rollar: admin / kassir / oshpaz)
AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- Ma'lumotlar bazasi ---
# DATABASE_URL orqali: dev'da SQLite, prod'da PostgreSQL (kod o'zgarmaydi)
DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3"),
}
# SQLite uchun fayl manzilini BASE_DIR ga bog'laymiz (CWD dan qat'i nazar)
if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    DATABASES["default"]["NAME"] = BASE_DIR / "db.sqlite3"

# --- Parol validatsiyasi ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Til / vaqt mintaqasi ---
LANGUAGE_CODE = env("LANGUAGE_CODE", default="uz")
TIME_ZONE = env("TIME_ZONE", default="Asia/Tashkent")
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("uz", "O'zbekcha"),
    ("ru", "Русский"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]

# --- Statik fayllar (CSS, JS, rasm) ---
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# --- Media fayllar (yuklangan rasmlar) ---
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- Sayt manzili (QR kodlar uchun to'liq URL yasashda ishlatiladi) ---
SITE_URL = env("SITE_URL", default="http://127.0.0.1:8000")

# --- Web Push (VAPID) ---
VAPID_PRIVATE_KEY_PATH = BASE_DIR / "vapid_private.pem"
VAPID_PUBLIC_KEY = env("VAPID_PUBLIC_KEY", default="")
VAPID_CLAIM_EMAIL = env("VAPID_CLAIM_EMAIL", default="mailto:admin@orderflow.uz")

# --- To'lov tizimlari (Payme / Click) ---
# Sandbox/test kalitlari .env faylida. Kalit bo'sh bo'lsa o'sha provayder
# webhook'i auth'dan o'tmaydi (integratsiya amalda o'chiq bo'ladi).
PAYMENT_TEST_MODE = env.bool("PAYMENT_TEST_MODE", default=True)

# Payme (Merchant API) — summa tiyinda, JSON-RPC, Basic auth
PAYME_MERCHANT_ID = env("PAYME_MERCHANT_ID", default="")
PAYME_MERCHANT_KEY = env("PAYME_MERCHANT_KEY", default="")  # test yoki prod kalit
PAYME_CHECKOUT_URL = env("PAYME_CHECKOUT_URL", default="https://checkout.test.paycom.uz")
PAYME_ACCOUNT_FIELD = env("PAYME_ACCOUNT_FIELD", default="order_id")  # hisob maydoni

# Click (SHOP API) — summa so'mda, form POST, md5 imzo
CLICK_SERVICE_ID = env("CLICK_SERVICE_ID", default="")
CLICK_MERCHANT_ID = env("CLICK_MERCHANT_ID", default="")
CLICK_SECRET_KEY = env("CLICK_SECRET_KEY", default="")
CLICK_MERCHANT_USER_ID = env("CLICK_MERCHANT_USER_ID", default="")
CLICK_PAY_URL = env("CLICK_PAY_URL", default="https://my.click.uz/services/pay")

# --- Xavfsizlik ---
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Production (DEBUG=False) da HTTPS va cookie himoyasi avtomatik yoqiladi
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# --- Django REST Framework ---
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "order": "20/min",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
