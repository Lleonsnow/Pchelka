"""
DRF-аутентификация по Telegram WebApp initData.
Передаём initData в заголовке X-Telegram-Init-Data.
"""
from django.conf import settings
from rest_framework import authentication

from apps.users.models import TelegramUser
from apps.api.telegram_auth import validate_init_data, get_telegram_user_from_validated


class TelegramWebAppAuthentication(authentication.BaseAuthentication):
    """Читает X-Telegram-Init-Data, валидирует и устанавливает request.telegram_user."""

    header = "X-Telegram-Init-Data"

    def authenticate(self, request):
        init_data = request.META.get(f"HTTP_{self.header.upper().replace('-', '_')}")
        if not init_data:
            # В режиме DEBUG можно тестировать WebApp в браузере без Telegram (задать DEV_WEBAPP_TELEGRAM_ID в .env)
            if getattr(settings, "DEBUG", False):
                dev_tid = getattr(settings, "DEV_WEBAPP_TELEGRAM_ID", "") or ""
                if dev_tid and dev_tid.isdigit():
                    telegram_user, _ = TelegramUser.objects.get_or_create(
                        telegram_id=int(dev_tid),
                        defaults={"username": "dev", "first_name": "Dev", "last_name": ""},
                    )
                    return (telegram_user, None)
            return None
        bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        if not bot_token:
            return None
        validated = validate_init_data(init_data, bot_token)
        if not validated:
            return None
        user_data = get_telegram_user_from_validated(validated)
        if not user_data:
            return None
        telegram_id = user_data.get("id")
        if not telegram_id:
            return None
        telegram_user, _ = TelegramUser.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                "username": user_data.get("username") or "",
                "first_name": user_data.get("first_name") or "",
                "last_name": user_data.get("last_name") or "",
            },
        )
        return (telegram_user, None)
