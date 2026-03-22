import logging
from typing import Any, Awaitable, Callable

from aiogram import Bot, BaseMiddleware
from aiogram.types import (
    TelegramObject,
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from bot.repositories.bot_settings_repository import (
    get_subscription_channels_cached,
    SubscriptionChannelData,
)

logger = logging.getLogger(__name__)


class SubscriptionMiddleware(BaseMiddleware):
    """Проверяет подписку на каналы из БД. Без подписки — сообщение и кнопки-ссылки."""

    def __init__(self, session_factory, get_session_func, bot: Bot):
        self.session_factory = session_factory
        self.get_session = get_session_func
        self.bot = bot

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Update):
            return await handler(event, data)

        # Проверку подписки применяем только к личным диалогам.
        if event.message and event.message.chat and event.message.chat.type != "private":
            return await handler(event, data)
        if event.callback_query and event.callback_query.message and event.callback_query.message.chat.type != "private":
            return await handler(event, data)

        user_id = None
        if event.message and event.message.from_user:
            user_id = event.message.from_user.id
        elif event.callback_query and event.callback_query.from_user:
            user_id = event.callback_query.from_user.id
        elif event.inline_query and event.inline_query.from_user:
            user_id = event.inline_query.from_user.id
        else:
            return await handler(event, data)

        channels = await get_subscription_channels_cached(
            self.session_factory, self.get_session
        )
        if not channels:
            return await handler(event, data)

        not_member: list[SubscriptionChannelData] = []
        for ch in channels:
            try:
                status = await self.bot.get_chat_member(chat_id=ch.channel_id, user_id=user_id)
                if status.status in ("left", "kicked"):
                    not_member.append(ch)
            except Exception as e:
                logger.warning("get_chat_member %s: %s", ch.channel_id, e)
                not_member.append(ch)

        if not not_member:
            return await handler(event, data)

        text = "Чтобы пользоваться ботом, подпишитесь на каналы:\n\n" + "\n".join(
            f"• {ch.title}" for ch in not_member
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=ch.title, url=ch.invite_link or f"https://t.me/{ch.channel_id}")]
                for ch in not_member
                if ch.invite_link
            ]
        )
        if not keyboard.inline_keyboard and not_member:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Перейти в канал", url=f"https://t.me/c/{str(not_member[0].channel_id).replace('-100', '')}")]
                ]
            )

        if event.message:
            await event.message.answer(text, reply_markup=keyboard)
        elif event.callback_query:
            await event.callback_query.answer("Сначала подпишитесь на каналы.", show_alert=True)
            if event.callback_query.message:
                await event.callback_query.message.answer(text, reply_markup=keyboard)
        return
