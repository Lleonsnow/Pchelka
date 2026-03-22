from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest

from bot.config import BotConfig
from bot.database import get_session
from bot.repositories import catalog_repository as repo
from bot.keyboards.catalog import (
    CatalogCallbackData,
    CartCallbackData,
    build_catalog_keyboard,
    product_card_keyboard,
)
from bot.utils.callback_edit import edit_callback_text

router = Router(name="catalog")
PER_PAGE = repo.PER_PAGE


def _media_base_url(config: BotConfig) -> str:
    return (config.media_base_url or "").rstrip("/")


def _webapp_base_url(config: BotConfig) -> str:
    return (config.webapp_url or "").strip()


def _tg_link_kw(config: BotConfig) -> dict[str, str]:
    return {
        "bot_username": (config.TELEGRAM_BOT_USERNAME or "").strip().lstrip("@"),
        "miniapp_short": (config.TELEGRAM_MINIAPP_SHORT_NAME or "").strip(),
    }


def _product_url(config: BotConfig, path: str) -> str:
    path = (path or "").strip().replace("\n", "").replace("\r", "")
    if not path:
        return ""
    base = _media_base_url(config)
    if not base:
        return ""
    return f"{base}/{path}" if not path.startswith("http") else path


async def _send_product_card(
    callback_or_message: CallbackQuery | Message,
    product: repo.ProductData,
    category_id: int,
    config: BotConfig,
    edit: bool = False,
) -> None:
    text = f"<b>{product.name}</b>\n\n{product.description or '—'}\n\n💰 {product.price} ₽"
    keyboard = product_card_keyboard(
        category_id,
        product.id,
        _webapp_base_url(config) or None,
        **_tg_link_kw(config),
    )
    if product.image_paths:
        urls = [_product_url(config, p) for p in product.image_paths if _product_url(config, p)]
        if urls:
            try:
                if len(urls) == 1:
                    if isinstance(callback_or_message, CallbackQuery):
                        cq = callback_or_message
                        await cq.bot.send_photo(
                            chat_id=cq.message.chat.id,
                            photo=urls[0],
                            caption=text,
                            reply_markup=keyboard,
                        )
                        if edit and cq.message:
                            try:
                                await cq.message.delete()
                            except TelegramBadRequest:
                                pass
                    else:
                        await callback_or_message.answer_photo(
                            photo=urls[0],
                            caption=text,
                            reply_markup=keyboard,
                        )
                    return
                media = [InputMediaPhoto(media=url) for url in urls]
                media[0].caption = text
                if isinstance(callback_or_message, CallbackQuery):
                    cq = callback_or_message
                    await cq.bot.send_media_group(chat_id=cq.message.chat.id, media=media)
                    await cq.bot.send_message(
                        chat_id=cq.message.chat.id,
                        text="🛒 Добавить в корзину?",
                        reply_markup=keyboard,
                    )
                    if edit and cq.message:
                        try:
                            await cq.message.delete()
                        except TelegramBadRequest:
                            pass
                else:
                    msg_target = callback_or_message
                    await msg_target.answer_media_group(media)
                    await msg_target.answer("🛒 Добавить в корзину?", reply_markup=keyboard)
                return
            except TelegramBadRequest:
                pass
    if edit and isinstance(callback_or_message, CallbackQuery):
        await edit_callback_text(callback_or_message, text, reply_markup=keyboard)
    else:
        target = callback_or_message.message if isinstance(callback_or_message, CallbackQuery) else callback_or_message
        await target.answer(text, reply_markup=keyboard)


@router.message(F.text.in_({"📁 Каталог", "Каталог"}))
@router.message(F.text == "/catalog")
async def catalog_root(message: Message, session_factory, config: BotConfig) -> None:
    async with get_session(session_factory) as session:
        categories = await repo.get_root_categories(session)
    if not categories:
        await message.answer("Каталог пока пуст.")
        return
    keyboard = build_catalog_keyboard(
        _webapp_base_url(config) or "",
        categories,
        category_id=0,
        parent_id=None,
        page=0,
        total_pages=1,
        is_products_view=False,
        **_tg_link_kw(config),
    )
    await message.answer("🍯 Выберите категорию:", reply_markup=keyboard)


@router.callback_query(CatalogCallbackData.filter(F.action == "root"))
async def catalog_cb_root(callback: CallbackQuery, session_factory, config: BotConfig) -> None:
    async with get_session(session_factory) as session:
        categories = await repo.get_root_categories(session)
    if not categories:
        await callback.answer("Каталог пуст.")
        return
    keyboard = build_catalog_keyboard(
        _webapp_base_url(config) or "",
        categories,
        category_id=0,
        parent_id=None,
        page=0,
        total_pages=1,
        is_products_view=False,
        **_tg_link_kw(config),
    )
    await edit_callback_text(callback, "🍯 Выберите категорию:", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(CatalogCallbackData.filter(F.action == "open"))
async def catalog_cb_open(callback: CallbackQuery, callback_data: CatalogCallbackData, session_factory, config: BotConfig) -> None:
    cat_id = callback_data.category_id
    async with get_session(session_factory) as session:
        if cat_id == 0:
            categories = await repo.get_root_categories(session)
            parent_id = None
        else:
            cat = await repo.get_category_by_id(session, cat_id)
            if not cat:
                await callback.answer("Категория не найдена.")
                return
            parent_id = cat.parent_id
            categories = await repo.get_child_categories(session, cat_id)
        children_count = await repo.get_children_count(session, cat_id) if cat_id else 0
        products_count = await repo.get_products_count_in_category(session, cat_id)

    if children_count > 0:
        keyboard = build_catalog_keyboard(
            _webapp_base_url(config) or "",
            categories,
            category_id=cat_id,
            parent_id=parent_id,
            page=0,
            total_pages=1,
            is_products_view=False,
            **_tg_link_kw(config),
        )
        await edit_callback_text(callback, "🍯 Выберите категорию:", reply_markup=keyboard)
    elif products_count > 0:
        async with get_session(session_factory) as session:
            products = await repo.get_products_in_category(session, cat_id, page=0, per_page=PER_PAGE)
        total_pages = (products_count + PER_PAGE - 1) // PER_PAGE
        lines = ["🍯 Товары:\n"] + [f"• {p.name} — {p.price} ₽" for p in products]
        product_buttons = [(p.name, CatalogCallbackData(action="product", product_id=p.id).pack()) for p in products]
        keyboard = build_catalog_keyboard(
            _webapp_base_url(config) or "",
            [],
            category_id=cat_id,
            parent_id=parent_id,
            page=0,
            total_pages=total_pages,
            is_products_view=True,
            product_buttons=product_buttons,
            **_tg_link_kw(config),
        )
        await edit_callback_text(callback, "\n".join(lines), reply_markup=keyboard)
    else:
        await callback.answer("Здесь пока нет товаров.")
        return
    await callback.answer()


@router.callback_query(CatalogCallbackData.filter(F.action == "products"))
async def catalog_cb_products(callback: CallbackQuery, callback_data: CatalogCallbackData, session_factory, config: BotConfig) -> None:
    cat_id = callback_data.category_id
    page = callback_data.page
    async with get_session(session_factory) as session:
        cat = await repo.get_category_by_id(session, cat_id)
        if not cat:
            await callback.answer("Категория не найдена.")
            return
        parent_id = cat.parent_id
        total = await repo.get_products_count_in_category(session, cat_id)
        products = await repo.get_products_in_category(session, cat_id, page=page, per_page=PER_PAGE)
    total_pages = (total + PER_PAGE - 1) // PER_PAGE
    lines = ["🍯 Товары:\n"] + [f"• {p.name} — {p.price} ₽" for p in products]
    product_buttons = [(p.name, CatalogCallbackData(action="product", product_id=p.id).pack()) for p in products]
    keyboard = build_catalog_keyboard(
        _webapp_base_url(config) or "",
        [],
        category_id=cat_id,
        parent_id=parent_id,
        page=page,
        total_pages=total_pages,
        is_products_view=True,
        product_buttons=product_buttons,
        **_tg_link_kw(config),
    )
    await edit_callback_text(callback, "\n".join(lines), reply_markup=keyboard)
    await callback.answer()


@router.callback_query(CatalogCallbackData.filter(F.action == "product"))
async def catalog_cb_product(callback: CallbackQuery, callback_data: CatalogCallbackData, session_factory, config: BotConfig) -> None:
    product_id = callback_data.product_id
    async with get_session(session_factory) as session:
        product = await repo.get_product_by_id(session, product_id)
    if not product:
        await callback.answer("Товар не найден.")
        return
    await _send_product_card(callback, product, product.category_id, config, edit=True)
    await callback.answer()


@router.callback_query(CatalogCallbackData.filter(F.action == "back"))
async def catalog_cb_back(callback: CallbackQuery, callback_data: CatalogCallbackData, session_factory, config: BotConfig) -> None:
    parent_id = callback_data.category_id
    if parent_id == 0:
        async with get_session(session_factory) as session:
            categories = await repo.get_root_categories(session)
        keyboard = build_catalog_keyboard(
            _webapp_base_url(config) or "",
            categories,
            category_id=0,
            parent_id=None,
            page=0,
            total_pages=1,
            is_products_view=False,
            **_tg_link_kw(config),
        )
        await edit_callback_text(callback, "🍯 Выберите категорию:", reply_markup=keyboard)
    else:
        async with get_session(session_factory) as session:
            cat = await repo.get_category_by_id(session, parent_id)
            if not cat:
                await callback.answer("Ошибка.")
                return
            categories = await repo.get_child_categories(session, parent_id)
            children_count = await repo.get_children_count(session, parent_id)
            products_count = await repo.get_products_count_in_category(session, parent_id)
        if children_count > 0:
            keyboard = build_catalog_keyboard(
                _webapp_base_url(config) or "",
                categories,
                category_id=parent_id,
                parent_id=cat.parent_id,
                page=0,
                total_pages=1,
                is_products_view=False,
                **_tg_link_kw(config),
            )
            await edit_callback_text(callback, "🍯 Выберите категорию:", reply_markup=keyboard)
        elif products_count > 0:
            async with get_session(session_factory) as session:
                products = await repo.get_products_in_category(session, parent_id, page=0, per_page=PER_PAGE)
            total_pages = (products_count + PER_PAGE - 1) // PER_PAGE
            lines = ["🍯 Товары:\n"] + [f"• {p.name} — {p.price} ₽" for p in products]
            product_buttons = [(p.name, CatalogCallbackData(action="product", product_id=p.id).pack()) for p in products]
            keyboard = build_catalog_keyboard(
                _webapp_base_url(config) or "",
                [],
                category_id=parent_id,
                parent_id=cat.parent_id,
                page=0,
                total_pages=total_pages,
                is_products_view=True,
                product_buttons=product_buttons,
                **_tg_link_kw(config),
            )
            await edit_callback_text(callback, "\n".join(lines), reply_markup=keyboard)
        else:
            await callback.answer("Пусто.")
    await callback.answer()


@router.callback_query(CartCallbackData.filter(F.action == "add"))
async def cart_add(
    callback: CallbackQuery,
    callback_data: CartCallbackData,
    user,
    session_factory,
) -> None:
    from bot.repositories.cart_repository import add_to_cart
    async with get_session(session_factory) as session:
        await add_to_cart(session, user.id, callback_data.product_id, 1)
    await callback.answer("Добавлено в корзину.")


async def show_product_card_by_id(
    message: Message,
    product_id: int,
    session_factory,
    config: BotConfig,
) -> bool:
    """Показать карточку товара по id (для deep link). Возвращает True если товар найден."""
    async with get_session(session_factory) as session:
        product = await repo.get_product_by_id(session, product_id)
    if not product:
        return False
    await _send_product_card(message, product, product.category_id, config, edit=False)
    return True
