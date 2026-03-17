from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


class CatalogCallbackData(CallbackData, prefix="cat"):
    action: str  # root, open, products, product, back
    category_id: int = 0
    product_id: int = 0
    page: int = 0


class CartCallbackData(CallbackData, prefix="cart"):
    action: str  # add, inc, dec, remove, clear, checkout, info
    product_id: int = 0
    item_id: int = 0  # cart_cartitem.id для inc/dec/remove/info


def build_catalog_keyboard(
    base_url: str,
    categories: list,
    category_id: int,
    parent_id: int | None,
    page: int,
    total_pages: int,
    is_products_view: bool,
    product_buttons: list[tuple[str, str]] | None = None,
) -> InlineKeyboardMarkup:
    """Клавиатура каталога: категории или товары с пагинацией и кнопкой WebApp.
    product_buttons: список (текст кнопки, callback_data) для списка товаров.
    """
    buttons = []

    if is_products_view:
        if product_buttons:
            for label, cb in product_buttons:
                buttons.append([InlineKeyboardButton(text=label, callback_data=cb)])
        nav = []
        if page > 0:
            nav.append(
                InlineKeyboardButton(
                    text="◀ Назад",
                    callback_data=CatalogCallbackData(
                        action="products",
                        category_id=category_id,
                        page=page - 1,
                    ).pack(),
                )
            )
        if page < total_pages - 1 and total_pages > 1:
            nav.append(
                InlineKeyboardButton(
                    text="Вперёд ▶",
                    callback_data=CatalogCallbackData(
                        action="products",
                        category_id=category_id,
                        page=page + 1,
                    ).pack(),
                )
            )
        if nav:
            buttons.append(nav)
        back_cat_id = parent_id if parent_id is not None else 0
        buttons.append([
            InlineKeyboardButton(
                text="📁 К категориям",
                callback_data=CatalogCallbackData(action="back", category_id=back_cat_id).pack(),
            )
        ])
    else:
        for cat in categories:
            buttons.append([
                InlineKeyboardButton(
                    text=cat.name,
                    callback_data=CatalogCallbackData(action="open", category_id=cat.id).pack(),
                )
            ])
        if category_id != 0:
            buttons.append([
                InlineKeyboardButton(
                    text="◀ Назад",
                    callback_data=CatalogCallbackData(action="back", category_id=parent_id or 0).pack(),
                )
            ])

    if base_url:
        buttons.append([
            InlineKeyboardButton(
                text="📱 Открыть каталог в браузере",
                web_app=WebAppInfo(url=base_url),
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_card_keyboard(category_id: int, product_id: int, base_url: str | None) -> InlineKeyboardMarkup:
    """Клавиатура карточки товара: В корзину + назад к категории + WebApp."""
    buttons = [
        [
            InlineKeyboardButton(
                text="🛒 В корзину",
                callback_data=CartCallbackData(action="add", product_id=product_id).pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text="◀ К категории",
                callback_data=CatalogCallbackData(action="open", category_id=category_id).pack(),
            )
        ],
    ]
    if base_url:
        buttons.append([
            InlineKeyboardButton(
                text="📱 Открыть в браузере",
                web_app=WebAppInfo(url=base_url),
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
