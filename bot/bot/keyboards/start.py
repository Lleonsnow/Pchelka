from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

REQUEST_CONTACT = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Поделиться контактом", request_contact=True)],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)


def get_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📁 Каталог"),
                KeyboardButton(text="🛒 Корзина"),
            ],
            [KeyboardButton(text="📋 Мои заказы")],
            [KeyboardButton(text="❓ Помощь")],
        ],
        resize_keyboard=True,
    )
