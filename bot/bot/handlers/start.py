import re

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import CommandStart, Command, CommandObject

from bot.config import BotConfig
from bot.database import get_session
from bot.repositories.user_repository import UserData, update_user_phone
from bot.keyboards.start import REQUEST_CONTACT, get_main_menu

router = Router(name="start")


def _extract_start_payload(message: Message, command: CommandObject) -> str:
    """
    Payload после /start (deep link t.me/bot?start=product_<id>).
    Иногда command.args пустой, а текст в message.text — учитываем /start@BotName.
    """
    raw = (command.args or "").strip()
    if raw:
        return raw.split()[0].lower()
    txt = (message.text or "").strip()
    if not txt:
        return ""
    parts = txt.split(maxsplit=1)
    if not parts[0].startswith("/start"):
        return ""
    if len(parts) < 2:
        return ""
    return parts[1].strip().lower().split()[0]


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    command: CommandObject,
    user: UserData,
    session_factory,
    config: BotConfig,
) -> None:
    args = _extract_start_payload(message, command)
    m_product = re.match(r"^product_(\d+)", args)
    if m_product:
        pid = int(m_product.group(1))
        from bot.handlers.catalog import show_product_card_by_id

        ok = await show_product_card_by_id(message, pid, session_factory, config)
        if ok and user.phone:
            await message.answer(
                "Выбери действие в меню ниже.",
                reply_markup=get_main_menu(),
            )
        elif ok:
            await message.answer(
                "Для заказов поделитесь контактом.",
                reply_markup=REQUEST_CONTACT,
            )
        else:
            await message.answer("Товар не найден.")
        return

    webapp_url = (config.webapp_url or "").strip()
    webapp_kb = (
        InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Открыть магазин", web_app=WebAppInfo(url=webapp_url))],
            ]
        )
        if webapp_url else None
    )

    if user.phone:
        await message.answer(
            f"Привет, {user.first_name or 'друг'}! 👋\n\n"
            "Нажми кнопку ниже или выбери действие в меню.",
            reply_markup=webapp_kb or get_main_menu(),
        )
        return
    await message.answer(
        "Добро пожаловать! Нажми «Открыть магазин» или поделитесь контактом для доставки заказов.",
        reply_markup=webapp_kb or REQUEST_CONTACT,
    )
    if webapp_kb:
        await message.answer("Поделиться контактом:", reply_markup=REQUEST_CONTACT)


@router.message(lambda m: m.contact is not None)
async def handle_contact(
    message: Message, user: UserData, session_factory, config: BotConfig
) -> None:
    if message.from_user and message.contact and message.from_user.id != message.contact.user_id:
        await message.answer("Пожалуйста, отправьте свой контакт.")
        return
    phone = (message.contact.phone_number or "").strip()
    if not phone:
        await message.answer("Не удалось получить номер телефона.")
        return
    async with get_session(session_factory) as session:
        await update_user_phone(session, user.telegram_id, phone)
    webapp_url = (config.webapp_url or "").strip()
    webapp_kb = (
        InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Открыть магазин", web_app=WebAppInfo(url=webapp_url))],
            ]
        )
        if webapp_url else None
    )
    await message.answer(
        "Спасибо! Контакт сохранён. Нажми кнопку ниже или выбери действие в меню.",
        reply_markup=webapp_kb or get_main_menu(),
    )
    if webapp_kb:
        await message.answer("Меню:", reply_markup=get_main_menu())


@router.message(F.text.in_({"📋 Мои заказы", "Мои заказы"}))
async def cmd_my_orders(message: Message, config: BotConfig) -> None:
    """Открыть раздел «Мои заказы» в Web App (в приложении — скролл при >4 заказов)."""
    webapp_url = (config.webapp_url or "").strip().rstrip("/")
    if not webapp_url:
        await message.answer("Магазин временно недоступен.")
        return
    profile_url = f"{webapp_url}/profile"
    await message.answer(
        "Откройте приложение, чтобы посмотреть историю заказов:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📋 Мои заказы", web_app=WebAppInfo(url=profile_url))],
            ]
        ),
    )


@router.message(Command("help"), F.chat.type == "private")
@router.message(F.text.in_({"❓ Помощь", "Помощь"}), F.chat.type == "private")
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Команды бота:\n"
        "/start — начать\n"
        "/catalog — каталог товаров\n"
        "/cart — корзина\n"
        "/help — эта справка\n\n"
        "Частые вопросы: в любом чате наберите @имя_бота и строку поиска "
        "(пустой запрос — популярные вопросы); выберите пункт — ответ уйдёт в чат."
    )


