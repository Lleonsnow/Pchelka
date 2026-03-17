from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.database import get_session
from bot.repositories.user_repository import UserData
from bot.repositories.cart_repository import (
    get_cart_items,
    get_cart_total,
    update_cart_item_quantity,
    remove_cart_item,
    clear_cart,
)
from bot.keyboards.cart import build_cart_keyboard
from bot.keyboards.catalog import CartCallbackData
from bot.fsm.order import OrderFSM

router = Router(name="cart")


def _format_cart_message(items: list, total) -> str:
    if not items:
        return "🛒 Корзина пуста. Добавьте товары из каталога."
    lines = ["🛒 <b>Корзина</b>\n"]
    for item in items:
        lines.append(f"• {item.product_name} × {item.quantity} = {item.subtotal} ₽")
    lines.append(f"\n<b>Итого: {total} ₽</b>")
    return "\n".join(lines)


async def _send_cart(callback_or_message: CallbackQuery | Message, user: UserData, session_factory) -> None:
    async with get_session(session_factory) as session:
        items = await get_cart_items(session, user.id)
        total = await get_cart_total(session, user.id)
    text = _format_cart_message(items, total)
    keyboard = build_cart_keyboard(items)
    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.message.edit_text(text, reply_markup=keyboard)
    else:
        await callback_or_message.answer(text, reply_markup=keyboard)


@router.message(F.text.in_({"🛒 Корзина", "Корзина"}))
@router.message(F.text == "/cart")
async def cart_show(message: Message, user: UserData, session_factory) -> None:
    await _send_cart(message, user, session_factory)


@router.callback_query(CartCallbackData.filter(F.action == "info"))
async def cart_info(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(CartCallbackData.filter(F.action.in_({"inc", "dec"})))
async def cart_qty(
    callback: CallbackQuery,
    callback_data: CartCallbackData,
    user: UserData,
    session_factory,
) -> None:
    delta = 1 if callback_data.action == "inc" else -1
    async with get_session(session_factory) as session:
        still_exists = await update_cart_item_quantity(
            session, user.id, callback_data.item_id, delta
        )
    await _send_cart(callback, user, session_factory)
    await callback.answer("Количество обновлено" if still_exists else "Позиция удалена")


@router.callback_query(CartCallbackData.filter(F.action == "remove"))
async def cart_remove(
    callback: CallbackQuery,
    callback_data: CartCallbackData,
    user: UserData,
    session_factory,
) -> None:
    async with get_session(session_factory) as session:
        await remove_cart_item(session, user.id, callback_data.item_id)
    await _send_cart(callback, user, session_factory)
    await callback.answer("Позиция удалена")


@router.callback_query(CartCallbackData.filter(F.action == "clear"))
async def cart_clear(
    callback: CallbackQuery,
    user: UserData,
    session_factory,
) -> None:
    async with get_session(session_factory) as session:
        await clear_cart(session, user.id)
    await callback.message.edit_text("🛒 Корзина пуста. Добавьте товары из каталога.")
    await callback.answer("Корзина очищена")


@router.callback_query(CartCallbackData.filter(F.action == "checkout"))
async def cart_checkout(
    callback: CallbackQuery,
    user: UserData,
    session_factory,
    state: FSMContext,
) -> None:
    async with get_session(session_factory) as session:
        items = await get_cart_items(session, user.id)
    if not items:
        await callback.answer("Корзина пуста.", show_alert=True)
        return
    await state.set_state(OrderFSM.fio)
    await state.update_data(order_message_id=callback.message.message_id)
    await callback.message.edit_text(
        "Оформление заказа. Введите <b>ФИО</b> (например: Иванов Иван Иванович):"
    )
    await callback.answer()
