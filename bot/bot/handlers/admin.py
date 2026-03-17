from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery

from bot.database import get_session
from bot.repositories.bot_settings_repository import get_bot_settings_cached
from bot.repositories.order_repository import (
    get_order_for_admin,
    get_orders_list,
    set_order_status,
    get_order_user_telegram_id,
    ORDER_STATUS_LABELS,
)
from bot.filters.is_admin import IsAdminFilter
from bot.keyboards.admin import admin_order_keyboard

router = Router(name="admin")


def _format_order_for_admin(order: dict) -> str:
    lines = [
        f"📦 Заказ <b>#{order['id']}</b>",
        f"Статус: {ORDER_STATUS_LABELS.get(order['status'], order['status'])}",
        f"ФИО: {order['full_name']}",
        f"Адрес: {order['address']}",
        f"Телефон: {order['phone']}",
        f"Telegram ID: {order['telegram_id']}",
        f"Итого: {order['total']} ₽",
        "",
        "Позиции:",
    ]
    for item in order.get("items", []):
        lines.append(f"  • {item['name']} × {item['quantity']} = {item['price'] * item['quantity']} ₽")
    return "\n".join(lines)


async def notify_user_order_status(
    bot: Bot,
    session_factory,
    order_id: int,
    new_status: str,
) -> None:
    """Отправить пользователю уведомление о смене статуса заказа."""
    async with get_session(session_factory) as session:
        telegram_id = await get_order_user_telegram_id(session, order_id)
    if not telegram_id:
        return
    label = ORDER_STATUS_LABELS.get(new_status, new_status)
    try:
        await bot.send_message(
            telegram_id,
            f"Статус вашего заказа <b>#{order_id}</b> изменён: <b>{label}</b>.",
        )
    except Exception:
        pass


@router.message(F.text == "/orders", IsAdminFilter())
async def cmd_orders(message: Message, session_factory) -> None:
    """Список последних заказов (только для админов)."""
    async with get_session(session_factory) as session:
        orders = await get_orders_list(session, limit=15)
    if not orders:
        await message.answer("Заказов пока нет.")
        return
    lines = ["📋 <b>Последние заказы</b>\n"]
    for o in orders:
        label = ORDER_STATUS_LABELS.get(o["status"], o["status"])
        lines.append(f"#{o['id']} — {o['full_name']} — {o['total']} ₽ — {label}")
    await message.answer("\n".join(lines))


@router.callback_query(F.data.startswith("adm_o_"), IsAdminFilter())
async def admin_order_status_cb(
    callback: CallbackQuery,
    session_factory,
    bot: Bot,
) -> None:
    """Смена статуса заказа из админ-чата."""
    parts = callback.data.split("_", 3)  # adm, o, order_id, status
    if len(parts) != 4:
        await callback.answer("Ошибка.")
        return
    try:
        order_id = int(parts[2])
        new_status = parts[3]
    except ValueError:
        await callback.answer("Ошибка.")
        return
    if new_status not in ORDER_STATUS_LABELS:
        await callback.answer("Неверный статус.")
        return
    async with get_session(session_factory) as session:
        ok = await set_order_status(session, order_id, new_status)
    if not ok:
        await callback.answer("Заказ не найден.", show_alert=True)
        return
    await notify_user_order_status(bot, session_factory, order_id, new_status)
    label = ORDER_STATUS_LABELS.get(new_status, new_status)
    await callback.message.edit_text(
        callback.message.text + f"\n\n✅ Статус обновлён на: {label}",
        reply_markup=admin_order_keyboard(order_id, new_status),
    )
    await callback.answer(f"Статус: {label}")
