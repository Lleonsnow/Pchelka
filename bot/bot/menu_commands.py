"""
Меню команд Telegram (кнопка «Меню» / список рядом с вводом).

Для админ-чата — отдельный scope BotCommandScopeChat (только группы/супергруппы:
в каналах Telegram API не даёт setMyCommands — команды только вручную через /).
"""
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat,
    MenuButtonCommands,
)

from bot.database import get_session
from bot.repositories.bot_settings_repository import get_bot_settings

logger = logging.getLogger(__name__)

BOT_COMMANDS_PRIVATE = [
    BotCommand(command="start", description="Начать"),
    BotCommand(command="catalog", description="Каталог"),
    BotCommand(command="cart", description="Корзина"),
    BotCommand(command="help", description="Помощь"),
]

# Любая группа / супергруппа (до привязки админ-чата или для чужих групп)
BOT_COMMANDS_GROUP_MINIMAL = [
    BotCommand(
        command="bind_admin_chat",
        description="Привязать этот чат для уведомлений админам",
    ),
    BotCommand(command="help", description="Справка по командам в этом чате"),
]

# Только для chat_id из BotSettings.admin_chat_id (группа, супергруппа или канал)
GROUP_HELP_BASIC = (
    "<b>Команды в группе / канале</b>\n\n"
    "/bind_admin_chat — привязать этот чат для уведомлений админам "
    "(работает, пока в настройках бота ещё не указан другой админ-чат).\n\n"
    "Полный список админ-команд — в <b>привязанном админ-чате</b>: отправьте "
    "<code>/help</code> там (или в личке с ботом — обычная справка для покупателей)."
)


def build_admin_chat_help_html() -> str:
    """Текст /help для привязанного админ-чата (группа / супергруппа / канал)."""
    lines = ["<b>Админ-чат — доступные команды</b>\n"]
    for c in BOT_COMMANDS_ADMIN_CHAT:
        lines.append(f"/{c.command} — {c.description}")
    lines.append(
        "\nℹ️ В <b>каналах</b> нет меню команд у поля ввода — публикуйте пост с текстом "
        "вида <code>/broadcasts</code> или <code>/orders</code>."
    )
    return "\n".join(lines)


BOT_COMMANDS_ADMIN_CHAT = [
    BotCommand(
        command="bind_admin_chat",
        description="Проверить привязку этого чата",
    ),
    BotCommand(command="orders", description="Последние заказы"),
    BotCommand(command="active_orders", description="Активные заказы"),
    BotCommand(command="broadcasts", description="Шаблоны рассылок"),
    BotCommand(command="broadcast_log", description="История рассылок"),
    BotCommand(
        command="broadcast_send",
        description="Отправить шаблон: /broadcast_send N",
    ),
    BotCommand(command="help", description="Справка по командам админ-чата"),
]


async def apply_all_command_scopes(bot: Bot, session_factory) -> None:
    """Выставить команды для личек, всех групп и (если задан) админ-чата."""
    await bot.set_my_commands(BOT_COMMANDS_PRIVATE, scope=BotCommandScopeAllPrivateChats())
    await bot.set_my_commands(
        BOT_COMMANDS_GROUP_MINIMAL,
        scope=BotCommandScopeAllGroupChats(),
    )
    await refresh_admin_chat_commands(bot, session_factory)


async def refresh_admin_chat_commands(
    bot: Bot,
    session_factory,
    *,
    admin_chat_id: int | None = None,
) -> None:
    """
    Повесить полное админ-меню на конкретный чат.
    Если admin_chat_id не передан — читается из БД.
    """
    cid = admin_chat_id
    if cid is None:
        async with get_session(session_factory) as session:
            settings = await get_bot_settings(session)
        cid = settings.admin_chat_id if settings else None
    if cid is None:
        logger.info("admin_chat_id не задан — команды для админ-чата не выставлены")
        return

    try:
        await bot.set_my_commands(
            BOT_COMMANDS_ADMIN_CHAT,
            scope=BotCommandScopeChat(chat_id=cid),
        )
        logger.info("Админ-команды (scope чата) для chat_id=%s", cid)
    except TelegramBadRequest as e:
        msg = (e.message or "").lower()
        if "channel" in msg and "command" in msg:
            logger.warning(
                "Админ-чат — канал: Telegram не позволяет setMyCommands для каналов "
                "(chat_id=%s). Команды вводите вручную: /broadcasts, /orders и т.д.",
                cid,
            )
        else:
            logger.exception("set_my_commands для admin chat_id=%s", cid)

    try:
        await bot.set_chat_menu_button(
            chat_id=cid,
            menu_button=MenuButtonCommands(),
        )
        logger.info("Кнопка меню «Команды» для chat_id=%s", cid)
    except TelegramBadRequest as e:
        msg = (e.message or "").lower()
        if "channel" in msg:
            logger.warning(
                "Для канала chat_id=%s кнопка меню команд недоступна в API Telegram.",
                cid,
            )
        else:
            logger.warning("set_chat_menu_button chat_id=%s: %s", cid, e)
