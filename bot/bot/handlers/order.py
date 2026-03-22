from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from bot.database import get_session
from bot.repositories.user_repository import UserData
from bot.repositories.cart_repository import get_cart_items, get_cart_total
from bot.repositories.order_repository import (
    create_order_from_cart,
    set_order_status,
    ORDER_STATUS_PAID,
)
from bot.fsm.order import OrderFSM
from bot.keyboards.start import get_main_menu
from bot.utils.callback_edit import edit_callback_text

router = Router(name="order")


@router.message(OrderFSM.fio, F.text)
async def order_fio(message: Message, user: UserData, state: FSMContext, session_factory) -> None:
    fio = (message.text or "").strip()
    if len(fio) < 2:
        await message.answer("Введите ФИО (минимум 2 символа).")
        return
    await state.update_data(fio=fio)
    await state.set_state(OrderFSM.address)
    await message.answer("Введите <b>адрес доставки</b>:")


@router.message(OrderFSM.address, F.text)
async def order_address(
    message: Message,
    user: UserData,
    state: FSMContext,
    session_factory,
) -> None:
    address = (message.text or "").strip()
    if len(address) < 5:
        await message.answer("Введите адрес (минимум 5 символов).")
        return
    await state.update_data(address=address)
    data = await state.get_data()
    fio = data.get("fio", "")
    async with get_session(session_factory) as session:
        items = await get_cart_items(session, user.id)
        total = await get_cart_total(session, user.id)
    lines = [
        "Подтвердите заказ:",
        f"ФИО: {fio}",
        f"Адрес: {address}",
        f"Телефон: {user.phone or '—'}",
        "",
        "Товары:",
    ]
    for item in items:
        lines.append(f"• {item.product_name} × {item.quantity} = {item.subtotal} ₽")
    lines.append(f"\n<b>Итого: {total} ₽</b>")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="order_confirm")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="order_cancel")],
    ])
    await state.set_state(OrderFSM.confirm)
    await message.answer("\n".join(lines), reply_markup=keyboard)


@router.callback_query(OrderFSM.confirm, F.data == "order_confirm")
async def order_confirm_cb(
    callback: CallbackQuery,
    user: UserData,
    state: FSMContext,
    session_factory,
) -> None:
    from bot.repositories.bot_settings_repository import get_bot_settings_cached
    from bot.repositories.order_repository import get_order_for_admin
    from bot.handlers.admin import _format_order_for_admin
    from bot.keyboards.admin import admin_order_keyboard

    data = await state.get_data()
    fio = data.get("fio", "")
    address = data.get("address", "")
    phone = user.phone or ""
    async with get_session(session_factory) as session:
        order_id = await create_order_from_cart(session, user.id, fio, address, phone)
    await state.clear()
    if not order_id:
        await edit_callback_text(callback, "Корзина пуста. Заказ не создан.")
        await callback.answer()
        return
    # Уведомление в админ-чат
    settings = await get_bot_settings_cached(session_factory, get_session)
    if settings and settings.admin_chat_id:
        async with get_session(session_factory) as session:
            order_data = await get_order_for_admin(session, order_id)
        if order_data:
            text = _format_order_for_admin(order_data)
            keyboard = admin_order_keyboard(order_id, order_data["status"])
            try:
                await callback.bot.send_message(
                    settings.admin_chat_id,
                    text,
                    reply_markup=keyboard,
                )
            except Exception:
                pass
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил(а)", callback_data=f"order_paid_{order_id}")],
    ])
    await edit_callback_text(
        callback,
        f"Заказ <b>#{order_id}</b> создан. Статус: ожидает оплаты.\n\n"
        "После оплаты нажмите кнопку ниже.",
        reply_markup=keyboard,
    )
    await callback.answer("Заказ создан")


@router.callback_query(OrderFSM.confirm, F.data == "order_cancel")
async def order_cancel_cb(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await edit_callback_text(callback, "Оформление заказа отменено.")
    await callback.answer()


@router.callback_query(F.data.startswith("order_paid_"))
async def order_paid_cb(
    callback: CallbackQuery,
    user: UserData,
    session_factory,
) -> None:
    try:
        order_id = int(callback.data.replace("order_paid_", ""))
    except ValueError:
        await callback.answer("Ошибка.")
        return
    async with get_session(session_factory) as session:
        ok = await set_order_status(session, order_id, ORDER_STATUS_PAID)
    if ok:
        await edit_callback_text(callback, f"Заказ #{order_id} отмечен как оплачен. Спасибо!")
    else:
        await callback.answer("Заказ не найден.", show_alert=True)
        return
    await callback.answer()
