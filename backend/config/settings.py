from pathlib import Path

from config.env_settings import EnvSettings

_env = EnvSettings()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = _env.SECRET_KEY
DEBUG = _env.DEBUG
ALLOWED_HOSTS = _env.allowed_hosts_list

BOT_INTERNAL_URL = _env.BOT_INTERNAL_URL or ""
TELEGRAM_BOT_TOKEN = (getattr(_env, "BOT_TOKEN", "") or "").strip()
TELEGRAM_WEBAPP_HOST = getattr(_env, "TELEGRAM_WEBAPP_HOST", "") or ""
DEV_WEBAPP_TELEGRAM_ID = getattr(_env, "DEV_WEBAPP_TELEGRAM_ID", "") or ""

CORS_ALLOWED_ORIGINS = list({
    *([] if not TELEGRAM_WEBAPP_HOST else [TELEGRAM_WEBAPP_HOST.rstrip("/")]),
    *(
        [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost",
            "http://127.0.0.1",
        ]
        if DEBUG
        else []
    ),
})

# Иначе браузер при preflight (запрос с кастомным заголовком) не отправит X-Telegram-Init-Data
CORS_ALLOW_HEADERS = (
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "origin",
    "user-agent",
    "x-requested-with",
    "x-telegram-init-data",
)

# За nginx/ngrok: доверять X-Forwarded-Proto для HTTPS и CSRF
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
_host = TELEGRAM_WEBAPP_HOST.strip().rstrip("/")
CSRF_TRUSTED_ORIGINS = [_host] if _host else []

# Безопасность в production (HTTPS за прокси)
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

INSTALLED_APPS = [
    "corsheaders",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.catalog",
    "apps.users",
    "apps.cart",
    "apps.orders.apps.OrdersConfig",
    "apps.faq",
    "apps.broadcasts",
    "apps.bot_settings",
    "rest_framework",
    "apps.api",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _env.POSTGRES_DB,
        "USER": _env.POSTGRES_USER,
        "PASSWORD": _env.POSTGRES_PASSWORD,
        "HOST": _env.POSTGRES_HOST,
        "PORT": _env.POSTGRES_PORT,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.api.auth.TelegramWebAppAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "apps.api.permissions.TelegramUserRequired",
    ],
}

_log_dir = BASE_DIR / "logs"
_log_dir.mkdir(parents=True, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": _log_dir / "backend.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
        },
        "console": {
            "level": "DEBUG" if DEBUG else "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
}
