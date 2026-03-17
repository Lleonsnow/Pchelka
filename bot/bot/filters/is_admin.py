from typing import Any

from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject, Message, CallbackQuery

from bot.database import get_session
from bot.repositories.bot_settings_repository import get_bot_settings_cached


class IsAdminFilter(BaseFilter):
    """Фильтр: True если telegram_id пользователя в admin_telegram_ids из BotSettings."""

    async def __call__(self, event: TelegramObject, data: dict[str, Any]) -> bool:
        user_id = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id
        if user_id is None:
            return False
        session_factory = data.get("session_factory")
        if not session_factory:
            return False
        settings = await get_bot_settings_cached(session_factory, get_session)
        if not settings or not settings.admin_telegram_ids:
            return False
        return user_id in settings.admin_telegram_ids
