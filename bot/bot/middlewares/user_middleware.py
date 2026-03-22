from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from bot.database import get_session
from bot.repositories.user_repository import UserData, get_or_create_user


class UserMiddleware(BaseMiddleware):
    """Проверяет/создаёт пользователя в БД и кладёт его в data["user"]."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        update = event
        if not isinstance(update, Update):
            return await handler(event, data)

        # Фабрика сессий нужна многим хендлерам (в т.ч. channel_post / bind_admin_chat).
        data["session_factory"] = self.session_factory

        from_user = None
        if update.message:
            from_user = update.message.from_user
        elif update.callback_query:
            from_user = update.callback_query.from_user
        elif update.inline_query:
            from_user = update.inline_query.from_user
        elif update.chat_member:
            from_user = update.chat_member.from_user
        elif update.my_chat_member:
            from_user = update.my_chat_member.from_user
        elif update.channel_post:
            from_user = update.channel_post.from_user
        elif update.edited_channel_post:
            from_user = update.edited_channel_post.from_user
        else:
            return await handler(event, data)

        if not from_user:
            return await handler(event, data)

        async with get_session(self.session_factory) as session:
            user = await get_or_create_user(
                session,
                telegram_id=from_user.id,
                username=from_user.username or "",
                first_name=from_user.first_name or "",
                last_name=from_user.last_name or "",
            )
        data["user"] = user
        return await handler(event, data)
