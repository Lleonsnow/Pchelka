import logging
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

logger = logging.getLogger(__name__)


def _get_update_type(update: Update) -> str:
    if update.message:
        return "message"
    if update.edited_message:
        return "edited_message"
    if update.channel_post:
        return "channel_post"
    if update.callback_query:
        return "callback_query"
    if update.inline_query:
        return "inline_query"
    if update.chosen_inline_result:
        return "chosen_inline_result"
    if update.shipping_query:
        return "shipping_query"
    if update.pre_checkout_query:
        return "pre_checkout_query"
    if update.poll:
        return "poll"
    if update.chat_member:
        return "chat_member"
    if update.my_chat_member:
        return "my_chat_member"
    return "unknown"


def _get_telegram_id(update: Update) -> int | None:
    if update.message and update.message.from_user:
        return update.message.from_user.id
    if update.callback_query and update.callback_query.from_user:
        return update.callback_query.from_user.id
    if update.inline_query and update.inline_query.from_user:
        return update.inline_query.from_user.id
    if update.chat_member:
        return update.chat_member.from_user.id if update.chat_member.from_user else None
    if update.my_chat_member:
        return update.my_chat_member.from_user.id if update.my_chat_member.from_user else None
    return None


class LoggingMiddleware(BaseMiddleware):
    """Логирует telegram_id, тип апдейта и timestamp."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Update):
            tg_id = _get_telegram_id(event)
            update_type = _get_update_type(event)
            ts = datetime.now(timezone.utc).isoformat()
            logger.info("update telegram_id=%s type=%s timestamp=%s", tg_id, update_type, ts)
        return await handler(event, data)
