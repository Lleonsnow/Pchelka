"""
DRF-аутентификация по Telegram WebApp initData.
Передаём initData в заголовке X-Telegram-Init-Data.
"""
import logging

from django.conf import settings
from rest_framework import authentication

from apps.users.models import TelegramUser
from apps.api.telegram_auth import (
    validate_init_data,
    get_telegram_user_from_validated,
    get_validation_failure_reason,
)

logger = logging.getLogger(__name__)


class TelegramWebAppAuthentication(authentication.BaseAuthentication):
    """Читает X-Telegram-Init-Data, валидирует и устанавливает request.telegram_user."""

    header = "X-Telegram-Init-Data"

    def authenticate(self, request):
        # Django META: X-Telegram-Init-Data → HTTP_X_TELEGRAM_INIT_DATA
        meta_key = "HTTP_" + self.header.upper().replace("-", "_")
        init_data = request.META.get(meta_key)
        if not init_data:
            logger.info(
                "[WebApp auth] 401: заголовок X-Telegram-Init-Data пуст или отсутствует. "
                "Ключ в META: %r, есть ли похожие: %s",
                meta_key,
                [k for k in request.META if "TELEGRAM" in k or "INIT" in k],
            )
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
            logger.info("[WebApp auth] 401: TELEGRAM_BOT_TOKEN не задан в настройках")
            return None
        validated = validate_init_data(init_data, bot_token)
        if not validated:
            reason = get_validation_failure_reason() or "unknown"
            logger.info(
                "[WebApp auth] 401: невалидный initData. Причина: %s. "
                "Откройте магазин из кнопки меню бота в Telegram (не по прямой ссылке).",
                reason,
            )
            return None
        user_data = get_telegram_user_from_validated(validated)
        if not user_data:
            logger.info("[WebApp auth] 401: в initData отсутствует объект user")
            return None
        telegram_id = user_data.get("id")
        if not telegram_id:
            return None
        telegram_user, _ = TelegramUser.objects.update_or_create(
            telegram_id=telegram_id,
            defaults={
                "username": user_data.get("username") or "",
                "first_name": user_data.get("first_name") or "",
                "last_name": user_data.get("last_name") or "",
            },
        )
        return (telegram_user, None)
