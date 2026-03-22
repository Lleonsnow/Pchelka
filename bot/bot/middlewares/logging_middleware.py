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
    if update.channel_post and update.channel_post.from_user:
        return update.channel_post.from_user.id
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
            chat_id = None
            chat_type = None
            text_preview = None
            if event.message and event.message.chat:
                chat_id = event.message.chat.id
                chat_type = event.message.chat.type
                text_preview = (event.message.text or event.message.caption or "")[:120]
            elif event.channel_post and event.channel_post.chat:
                chat_id = event.channel_post.chat.id
                chat_type = event.channel_post.chat.type
                text_preview = (event.channel_post.text or event.channel_post.caption or "")[:120]
            elif event.my_chat_member and event.my_chat_member.chat:
                chat_id = event.my_chat_member.chat.id
                chat_type = event.my_chat_member.chat.type
                text_preview = f"new_status={event.my_chat_member.new_chat_member.status}"
            elif event.callback_query:
                if event.callback_query.message and event.callback_query.message.chat:
                    chat_id = event.callback_query.message.chat.id
                    chat_type = event.callback_query.message.chat.type
                text_preview = (event.callback_query.data or "")[:120]
            logger.info(
                "update telegram_id=%s type=%s chat_id=%s chat_type=%s text=%r timestamp=%s",
                tg_id,
                update_type,
                chat_id,
                chat_type,
                text_preview,
                ts,
            )
        return await handler(event, data)
