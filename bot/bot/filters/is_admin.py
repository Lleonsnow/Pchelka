from typing import Any

from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject, Message, CallbackQuery

from bot.database import get_session
from bot.repositories.bot_settings_repository import get_bot_settings_cached


class IsAdminFilter(BaseFilter):
    """
    Доступ админ-функций:
    - если в BotSettings задан непустой admin_telegram_ids — только эти id;
    - если список пуст, но задан admin_chat_id — любой, кто жмёт в этом чате/канале
      (типичный случай после /bind_admin_chat без ручного заполнения id в Django).
    """

    async def __call__(self, event: TelegramObject, **kwargs: Any) -> bool:
        """Aiogram передаёт контекст в kwargs (не вторым позиционным data — иначе TypeError)."""
        user_id = None
        chat_id = None
        if isinstance(event, Message):
            if event.from_user:
                user_id = event.from_user.id
            if event.chat:
                chat_id = event.chat.id
        elif isinstance(event, CallbackQuery):
            if event.from_user:
                user_id = event.from_user.id
            if event.message and event.message.chat:
                chat_id = event.message.chat.id
        session_factory = kwargs.get("session_factory")
        if not session_factory:
            return False
        settings = await get_bot_settings_cached(session_factory, get_session)
        if not settings:
            return False

        if user_id is not None:
            if settings.admin_telegram_ids:
                return user_id in settings.admin_telegram_ids
            if settings.admin_chat_id is not None and chat_id == settings.admin_chat_id:
                return True
            return False

        # Пост в канале без from_user (типично для channel_post) — проверить личность нельзя.
        if (
            isinstance(event, Message)
            and event.chat
            and event.chat.type == "channel"
            and settings.admin_chat_id is not None
            and chat_id == settings.admin_chat_id
            and not settings.admin_telegram_ids
        ):
            return True
        return False
