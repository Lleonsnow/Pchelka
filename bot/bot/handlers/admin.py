import html
import logging

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ChatMemberUpdated

from bot.database import get_session
from bot.repositories.bot_settings_repository import (
    get_bot_settings_cached,
    get_bot_settings,
    set_admin_chat_id_if_empty,
)
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
logger = logging.getLogger(__name__)


async def _apply_bind_admin_chat(message: Message, session_factory) -> None:
    """Сохранить chat.id в admin_chat_id (если пусто)."""
    chat_id = message.chat.id if message.chat else None
    if not chat_id:
        return
    logger.info("bind_admin_chat: chat_id=%s chat_type=%s", chat_id, message.chat.type if message.chat else None)
    async with get_session(session_factory) as session:
        saved = await set_admin_chat_id_if_empty(session, chat_id)
        current = await get_bot_settings(session)
    logger.info(
        "bind_admin_chat result: chat_id=%s saved=%s current_admin_chat_id=%s",
        chat_id,
        saved,
        current.admin_chat_id if current else None,
    )
    if saved:
        await message.reply(f"✅ admin_chat_id сохранён: <code>{chat_id}</code>")
    else:
        current_id = current.admin_chat_id if current else None
        if current_id:
            await message.reply(
                f"ℹ️ admin_chat_id уже установлен: <code>{current_id}</code>"
            )
        else:
            await message.reply("⚠️ Не удалось сохранить admin_chat_id (проверьте BotSettings).")


def _format_order_for_admin(order: dict) -> str:
    tid = order["telegram_id"]
    raw_username = (order.get("username") or "").strip().lstrip("@")
    if raw_username:
        tag_line = (
            f"Тег: <a href=\"https://t.me/{html.escape(raw_username, quote=True)}\">"
            f"@{html.escape(raw_username)}</a> · <code>{tid}</code>"
        )
    else:
        tag_line = (
            f"Тег: <a href=\"tg://user?id={tid}\">написать в Telegram</a> · <code>{tid}</code> "
            f"(нет @username в профиле)"
        )
    lines = [
        f"📦 Заказ <b>#{order['id']}</b>",
        f"Статус: {html.escape(str(ORDER_STATUS_LABELS.get(order['status'], order['status'])))}",
        f"ФИО: {html.escape(str(order['full_name'] or ''))}",
        f"Адрес: {html.escape(str(order['address'] or ''))}",
        f"Телефон: {html.escape(str(order['phone'] or ''))}",
        tag_line,
        f"Итого: {order['total']} ₽",
        "",
        "Позиции:",
    ]
    for item in order.get("items", []):
        name = html.escape(str(item["name"]))
        lines.append(
            f"  • {name} × {item['quantity']} = {item['price'] * item['quantity']} ₽"
        )
    return "\n".join(lines)


@router.message(
    lambda m: (
        m.chat is not None
        and m.chat.type in {"group", "supergroup"}
        and not ((m.text or "").strip().startswith("/"))
    )
)
async def capture_admin_chat_once(message: Message, session_factory) -> None:
    """
    Автосохранение chat_id по обычному тексту в группе.

    Важно (Telegram Group Privacy / privacy mode, по умолчанию ON):
    бот в группах не получает произвольные сообщения — только команды (/...),
    ответы на сообщения бота и упоминания @username бота.
    Поэтому без отключения privacy или без команды /bind_admin_chat этот хендлер
    почти никогда не вызывается. См. https://core.telegram.org/bots/features#privacy-mode
    """
    chat_id = message.chat.id if message.chat else None
    if not chat_id:
        return
    logger.info(
        "Group message observed for admin_chat capture: chat_id=%s user_id=%s text=%r",
        chat_id,
        message.from_user.id if message.from_user else None,
        (message.text or "")[:80],
    )
    async with get_session(session_factory) as session:
        saved = await set_admin_chat_id_if_empty(session, chat_id)
    logger.info(
        "Attempted admin_chat_id save from group message: chat_id=%s saved=%s",
        chat_id,
        saved,
    )


@router.message(Command("bind_admin_chat"), F.chat.type == "private")
async def bind_admin_chat_private(message: Message) -> None:
    """Команда работает только в группе, супергруппе или канале (не в личке)."""
    await message.answer(
        "Эту команду нужно отправить <b>в группе, супергруппе или в канале</b>, "
        "куда добавлен бот (как админ для канала).\n\n"
        "В личном чате привязать чат нельзя — Telegram не передаёт сюда chat_id группы.\n\n"
        "Пример: <code>/bind_admin_chat</code> или "
        "<code>/bind_admin_chat@имя_бота</code>"
    )


@router.message(
    Command("bind_admin_chat"),
    lambda m: m.chat is not None and m.chat.type in {"group", "supergroup"},
)
async def bind_admin_chat_group(message: Message, session_factory) -> None:
    """
    Привязка в группе/супергруппе. При нескольких ботах: /bind_admin_chat@bot
    """
    await _apply_bind_admin_chat(message, session_factory)


@router.channel_post(Command("bind_admin_chat"))
async def bind_admin_chat_channel_post(message: Message, session_factory) -> None:
    """В канале посты приходят как channel_post, не как message."""
    await _apply_bind_admin_chat(message, session_factory)


@router.my_chat_member()
async def capture_admin_chat_on_member_update(event: ChatMemberUpdated, session_factory) -> None:
    """
    Резервный автозахват admin_chat_id на событии статуса бота в группе.
    Срабатывает даже если privacy mode запрещает чтение обычных сообщений.
    """
    chat = event.chat
    if not chat or chat.type not in {"group", "supergroup", "channel"}:
        return
    status = event.new_chat_member.status
    if status not in {"member", "administrator"}:
        return
    logger.info(
        "my_chat_member observed for admin_chat capture: chat_id=%s new_status=%s",
        chat.id,
        status,
    )
    async with get_session(session_factory) as session:
        saved = await set_admin_chat_id_if_empty(session, chat.id)
    logger.info(
        "Attempted admin_chat_id save from my_chat_member: chat_id=%s saved=%s",
        chat.id,
        saved,
    )


async def notify_admin_new_order(
    bot: Bot,
    session_factory,
    order_id: int,
) -> None:
    """Уведомить админ-чат о новом заказе (WebApp API и т.п.; в боте FSM — своё уведомление)."""
    settings = await get_bot_settings_cached(session_factory, get_session)
    if not settings or not settings.admin_chat_id:
        return
    async with get_session(session_factory) as session:
        order_data = await get_order_for_admin(session, order_id)
    if not order_data:
        return
    text = _format_order_for_admin(order_data)
    keyboard = admin_order_keyboard(order_id, order_data["status"])
    try:
        await bot.send_message(
            settings.admin_chat_id,
            text,
            reply_markup=keyboard,
        )
    except Exception:
        pass


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
    logger.info(
        "admin_order_status: order_id=%s new_status=%s from_user_id=%s chat_id=%s",
        order_id,
        new_status,
        callback.from_user.id if callback.from_user else None,
        callback.message.chat.id if callback.message and callback.message.chat else None,
    )
    async with get_session(session_factory) as session:
        ok = await set_order_status(session, order_id, new_status)
    if not ok:
        await callback.answer("Заказ не найден.", show_alert=True)
        return
    await notify_user_order_status(bot, session_factory, order_id, new_status)
    label = ORDER_STATUS_LABELS.get(new_status, new_status)
    async with get_session(session_factory) as session:
        order_data = await get_order_for_admin(session, order_id)
    if not order_data:
        await callback.answer("Не удалось обновить сообщение.", show_alert=True)
        return
    text = _format_order_for_admin(order_data)
    text += f"\n\n<b>✅ Статус обновлён:</b> {html.escape(label)}"
    try:
        await callback.message.edit_text(
            text,
            reply_markup=admin_order_keyboard(order_id, new_status),
        )
    except Exception:
        logger.exception("admin_order_status: edit_message failed order_id=%s", order_id)
        await callback.answer("Статус сохранён, но не удалось обновить сообщение.", show_alert=True)
        return
    await callback.answer(f"Статус: {label}")


@router.callback_query(F.data.startswith("adm_o_"))
async def admin_order_callback_no_access(callback: CallbackQuery) -> None:
    """Если IsAdminFilter не пропустил — ответить, иначе кнопка «крутится» бесконечно."""
    await callback.answer(
        "Нет доступа: укажите свой Telegram ID в админке (BotSettings → admin_telegram_ids) "
        "или оставьте список пустым и жмите кнопки только в привязанном админ-чате.",
        show_alert=True,
    )
