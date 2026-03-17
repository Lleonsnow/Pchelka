from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.keyboards.catalog import CartCallbackData


def build_cart_keyboard(items: list) -> InlineKeyboardMarkup:
    """Клавиатура корзины: для каждой позиции [-] название (qty) [+], удалить; внизу Очистить, Оформить заказ."""
    buttons = []
    for item in items:
        row = [
            InlineKeyboardButton(
                text="➖",
                callback_data=CartCallbackData(action="dec", item_id=item.id).pack(),
            ),
            InlineKeyboardButton(
                text=f"{item.product_name} ({item.quantity})",
                callback_data=CartCallbackData(action="info", item_id=item.id).pack(),
            ),
            InlineKeyboardButton(
                text="➕",
                callback_data=CartCallbackData(action="inc", item_id=item.id).pack(),
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=CartCallbackData(action="remove", item_id=item.id).pack(),
            ),
        ]
        buttons.append(row)
    if items:
        buttons.append([
            InlineKeyboardButton(
                text="🗑 Очистить корзину",
                callback_data=CartCallbackData(action="clear").pack(),
            )
        ])
        buttons.append([
            InlineKeyboardButton(
                text="✅ Оформить заказ",
                callback_data=CartCallbackData(action="checkout").pack(),
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons if buttons else [])
