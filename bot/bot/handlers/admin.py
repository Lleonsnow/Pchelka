import html
import logging

from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    Message,
    CallbackQuery,
    ChatMemberUpdated,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from bot.database import get_session
from bot.repositories.bot_settings_repository import (
    get_bot_settings_cached,
    get_bot_settings,
    set_admin_chat_id_if_empty,
)
from bot.repositories.order_repository import (
    get_order_for_admin,
    get_orders_list,
    get_active_orders_list,
    set_order_status,
    get_order_user_telegram_id,
    ORDER_STATUS_LABELS,
)
from bot.filters.is_admin import IsAdminFilter
from bot.keyboards.admin import admin_order_keyboard
from bot.repositories import broadcast_repository as broadcast_repo
from bot.menu_commands import (
    GROUP_HELP_BASIC,
    build_admin_chat_help_html,
    refresh_admin_chat_commands,
)
from bot.utils.callback_edit import edit_callback_text

router = Router(name="admin")
logger = logging.getLogger(__name__)


async def _apply_bind_admin_chat(message: Message, session_factory, bot: Bot) -> None:
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

    effective = current.admin_chat_id if current else None
    if effective == chat_id:
        await refresh_admin_chat_commands(bot, session_factory, admin_chat_id=chat_id)


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
async def bind_admin_chat_group(message: Message, session_factory, bot: Bot) -> None:
    """
    Привязка в группе/супергруппе. При нескольких ботах: /bind_admin_chat@bot
    """
    await _apply_bind_admin_chat(message, session_factory, bot)


@router.channel_post(Command("bind_admin_chat"))
async def bind_admin_chat_channel_post(message: Message, session_factory, bot: Bot) -> None:
    """В канале посты приходят как channel_post, не как message."""
    await _apply_bind_admin_chat(message, session_factory, bot)


@router.message(
    Command("help"),
    F.chat.type.in_({"group", "supergroup"}),
    IsAdminFilter(),
)
async def cmd_help_group_as_admin(message: Message) -> None:
    """Справка с полным списком админ-команд (привязанный админ-чат или whitelist id)."""
    await message.answer(build_admin_chat_help_html())


@router.message(Command("help"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_help_group_basic(message: Message) -> None:
    """Справка для прочих групп — только привязка и куда смотреть полный список."""
    await message.answer(GROUP_HELP_BASIC)


@router.channel_post(Command("help"), IsAdminFilter())
async def cmd_help_channel_as_admin(message: Message) -> None:
    await message.answer(build_admin_chat_help_html())


@router.channel_post(Command("help"))
async def cmd_help_channel_basic(message: Message) -> None:
    await message.answer(GROUP_HELP_BASIC)


@router.my_chat_member()
async def capture_admin_chat_on_member_update(
    event: ChatMemberUpdated, session_factory, bot: Bot
) -> None:
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
        current = await get_bot_settings(session)
    logger.info(
        "Attempted admin_chat_id save from my_chat_member: chat_id=%s saved=%s",
        chat.id,
        saved,
    )
    if current and current.admin_chat_id == chat.id:
        await refresh_admin_chat_commands(bot, session_factory, admin_chat_id=chat.id)


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


@router.message(Command("orders"), IsAdminFilter())
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
        fn = html.escape(str(o.get("full_name") or ""))
        lines.append(f"#{o['id']} — {fn} — {o['total']} ₽ — {html.escape(str(label))}")
    await message.answer("\n".join(lines))


@router.message(Command("active_orders"), IsAdminFilter())
async def cmd_active_orders(message: Message, session_factory) -> None:
    """Активные заказы: всё кроме «Доставлен» и «Отменён»."""
    async with get_session(session_factory) as session:
        orders = await get_active_orders_list(session, limit=30)
    if not orders:
        await message.answer("Активных заказов нет.")
        return
    lines = ["📬 <b>Активные заказы</b> <i>(не доставлены и не отменены)</i>\n"]
    for o in orders:
        label = ORDER_STATUS_LABELS.get(o["status"], o["status"])
        fn = html.escape(str(o.get("full_name") or ""))
        lines.append(f"#{o['id']} — {fn} — {o['total']} ₽ — {html.escape(str(label))}")
    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:3990] + "\n…"
    await message.answer(text)


_BROADCAST_STATUS_RU = {
    "draft": "черновик",
    "ready": "в очереди",
    "sent": "отправлено",
}


@router.message(Command("broadcasts"), IsAdminFilter())
async def cmd_broadcasts(message: Message, session_factory) -> None:
    """Список шаблонов и кнопки «Отправить»."""
    async with get_session(session_factory) as session:
        templates = await broadcast_repo.list_broadcast_templates(session, limit=20)
    if not templates:
        await message.answer(
            "Шаблонов нет. Создайте в админке Django: раздел «Шаблоны рассылок»."
        )
        return
    lines = ["📢 <b>Шаблоны рассылок</b>\n<i>Кнопка — поставить в очередь (бот отправит за несколько секунд).</i>\n"]
    for t in templates:
        lines.append(f"<b>#{t.id}</b> {html.escape(t.name)}")
        prev = (t.text or "").replace("\n", " ").strip()
        if len(prev) > 90:
            prev = prev[:87] + "…"
        if prev:
            lines.append(html.escape(prev))
        lines.append("")
    text = "\n".join(lines).strip()
    if len(text) > 3800:
        text = text[:3790] + "\n…"
    kb_rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text=f"📤 {(t.name[:30] + '…') if len(t.name) > 30 else t.name}",
                callback_data=f"bcs_{t.id}",
            )
        ]
        for t in templates
    ]
    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows),
    )


@router.message(Command("broadcast_log"), IsAdminFilter())
async def cmd_broadcast_log(message: Message, session_factory) -> None:
    """История рассылок (записи в БД)."""
    async with get_session(session_factory) as session:
        rows = await broadcast_repo.list_broadcast_history(session, limit=15)
    if not rows:
        await message.answer("Записей о рассылках пока нет.")
        return
    lines = ["📜 <b>Последние рассылки</b>\n"]
    for h in rows:
        st = _BROADCAST_STATUS_RU.get(h.status, h.status)
        preview = html.escape((h.text_preview or "").replace("\n", " "))
        lines.append(
            f"#{h.id} — <i>{html.escape(st)}</i> · ✓{h.delivered_count} ✗{h.error_count}\n{preview}\n"
        )
    out = "\n".join(lines).strip()
    if len(out) > 4000:
        out = out[:3990] + "\n…"
    await message.answer(out)


@router.message(Command("broadcast_send"), IsAdminFilter())
async def cmd_broadcast_send(
    message: Message,
    session_factory,
    command: CommandObject,
) -> None:
    """Отправка по номеру шаблона: /broadcast_send 2"""
    arg = (command.args or "").strip().split(maxsplit=1)[0]
    if not arg.isdigit():
        await message.answer(
            "Укажите номер шаблона из списка <code>/broadcasts</code>:\n"
            "<code>/broadcast_send 2</code>"
        )
        return
    tid = int(arg)
    async with get_session(session_factory) as session:
        bid = await broadcast_repo.enqueue_broadcast_from_template(session, tid)
    if bid is None:
        await message.answer(f"Шаблон <b>#{tid}</b> не найден или отключён.")
        return
    await message.answer(
        f"✅ Рассылка <b>#{bid}</b> поставлена в очередь. Бот отправит подписчикам в течение нескольких секунд."
    )


# В канале команды приходят как channel_post, не как message.
for _cmd, _handler in (
    ("orders", cmd_orders),
    ("active_orders", cmd_active_orders),
    ("broadcasts", cmd_broadcasts),
    ("broadcast_log", cmd_broadcast_log),
    ("broadcast_send", cmd_broadcast_send),
):
    router.channel_post.register(_handler, Command(_cmd), IsAdminFilter())


@router.callback_query(F.data.startswith("bcs_"), IsAdminFilter())
async def broadcast_send_callback(
    callback: CallbackQuery,
    session_factory,
) -> None:
    try:
        tid = int((callback.data or "").split("_", 1)[1])
    except (IndexError, ValueError):
        await callback.answer("Неверные данные.", show_alert=True)
        return
    async with get_session(session_factory) as session:
        bid = await broadcast_repo.enqueue_broadcast_from_template(session, tid)
    if bid is None:
        await callback.answer("Шаблон не найден или отключён.", show_alert=True)
        return
    await callback.answer(f"В очереди: рассылка #{bid}")
    if callback.message:
        await callback.message.reply(
            f"✅ Рассылка <b>#{bid}</b> поставлена в очередь (шаблон #{tid})."
        )


@router.callback_query(F.data.startswith("bcs_"))
async def broadcast_send_callback_denied(callback: CallbackQuery) -> None:
    await callback.answer("Нет доступа.", show_alert=True)


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
        await edit_callback_text(
            callback,
            text,
            reply_markup=admin_order_keyboard(order_id, new_status),
        )
    except Exception:
        logger.exception("admin_order_status: edit_or_send failed order_id=%s", order_id)
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
