from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.repositories.order_repository import ORDER_STATUS_LABELS


def admin_order_keyboard(order_id: int, current_status: str) -> InlineKeyboardMarkup:
    """Inline-кнопки смены статуса заказа для админ-чата. prefix adm_o_ чтобы уложиться в 64 байта."""
    buttons = []
    row = []
    for status, label in ORDER_STATUS_LABELS.items():
        if status == current_status:
            continue
        row.append(
            InlineKeyboardButton(
                text=label,
                callback_data=f"adm_o_{order_id}_{status}",
            )
        )
        if len(row) >= 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)
