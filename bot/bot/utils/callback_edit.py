from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest


async def edit_callback_text(
    callback: CallbackQuery,
    text: str,
    *,
    reply_markup=None,
) -> None:
    """
    Редактирует сообщение, к которому привязан callback. Если сообщение удалено,
    не текстовое или правка запрещена API — отправляет новое сообщение в тот же чат.
    """
    msg = callback.message
    if msg is None:
        await callback.bot.send_message(callback.from_user.id, text, reply_markup=reply_markup)
        return
    try:
        await msg.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest:
        await callback.bot.send_message(msg.chat.id, text, reply_markup=reply_markup)
