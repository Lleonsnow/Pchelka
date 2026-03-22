import re

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import CommandStart, Command, CommandObject

from bot.config import BotConfig
from bot.database import get_session
from bot.repositories.user_repository import UserData, update_user_phone
from bot.keyboards.start import REQUEST_CONTACT, get_main_menu

router = Router(name="start")

# Тексты /start: одно сообщение, без дубля с MenuButtonWebApp («Открыть магазин» у поля ввода).
_WELCOME_NO_PHONE_WEBAPP = (
    "Это <b>магазин в Telegram</b>: в мини-приложении — каталог, корзина и оформление заказа.\n\n"
    "Чтобы курьер мог с вами связаться, <b>один раз</b> нажмите «Поделиться контактом» ниже — "
    "номер сохраним в профиле.\n\n"
    "Мини-приложение открывается <b>синей кнопкой «Открыть магазин»</b> слева от поля ввода сообщения."
)
_WELCOME_NO_PHONE_NO_WEBAPP = (
    "Это <b>магазин в Telegram</b>. Чтобы оформлять заказы с доставкой, нажмите "
    "«Поделиться контактом» ниже — номер нужен для связи с вами."
)
_WELCOME_HAS_PHONE = (
    "{name}, с возвращением!\n\n"
    "Каталог и корзина — в <b>мини-приложении</b> (кнопка «Открыть магазин» слева от поля ввода) "
    "или через меню ниже."
)
_THANKS_CONTACT = (
    "Спасибо, контакт сохранили.\n\n"
    "Дальше — мини-приложение (кнопка «Открыть магазин» у поля ввода) или пункты меню ниже."
)


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
                "Чтобы оформить доставку, поделитесь контактом кнопкой ниже.",
                reply_markup=REQUEST_CONTACT,
            )
        else:
            await message.answer("Товар не найден.")
        return

    if user.phone:
        name = user.first_name or "друг"
        await message.answer(
            _WELCOME_HAS_PHONE.format(name=name),
            reply_markup=get_main_menu(),
        )
        return

    text = _WELCOME_NO_PHONE_WEBAPP if (config.webapp_url or "").strip() else _WELCOME_NO_PHONE_NO_WEBAPP
    await message.answer(text, reply_markup=REQUEST_CONTACT)


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
    await message.answer(_THANKS_CONTACT, reply_markup=get_main_menu())


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


