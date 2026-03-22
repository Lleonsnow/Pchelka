import asyncio
import logging
import logging.handlers
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    MenuButtonWebApp,
    WebAppInfo,
)
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BotConfig
from bot.database import create_session_factory, get_session
from bot.handlers import start as start_router
from bot.handlers import catalog as catalog_router
from bot.handlers import cart as cart_router
from bot.handlers import order as order_router
from bot.handlers import admin as admin_router
from bot.handlers import faq as faq_router
from bot.middlewares.config_middleware import ConfigMiddleware
from bot.middlewares.logging_middleware import LoggingMiddleware
from bot.middlewares.user_middleware import UserMiddleware
from bot.middlewares.subscription_middleware import SubscriptionMiddleware
from bot.notify_server import run_notify_server
from bot.broadcast_sender import run_broadcast_worker

_log_dir = Path(__file__).resolve().parent.parent / "logs"
_log_dir.mkdir(parents=True, exist_ok=True)

_handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
try:
    _handlers.append(
        logging.handlers.RotatingFileHandler(
            _log_dir / "bot.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
        )
    )
except PermissionError:
    # В volume-файле могут остаться root-права; не валим запуск бота из-за файла логов.
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=_handlers,
)
logger = logging.getLogger(__name__)

# Личные чаты: меню команд
BOT_COMMANDS_PRIVATE = [
    BotCommand(command="start", description="Начать"),
    BotCommand(command="catalog", description="Каталог"),
    BotCommand(command="cart", description="Корзина"),
    BotCommand(command="help", description="Помощь"),
]

# Группы / супергруппы: при включённом Group Privacy бот получает только команды (и реплаи/упоминания),
# обычный текст в группу боту не доставляется — см. https://core.telegram.org/bots/features#privacy-mode
BOT_COMMANDS_GROUP = [
    BotCommand(
        command="bind_admin_chat",
        description="Привязать этот чат для уведомлений админам",
    ),
]


async def main() -> None:
    config = BotConfig()
    session_factory = create_session_factory(config)
    bot = Bot(
        token=config.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.update.middleware(ConfigMiddleware(config))
    dp.update.middleware(LoggingMiddleware())
    dp.update.middleware(UserMiddleware(session_factory))
    dp.update.middleware(SubscriptionMiddleware(session_factory, get_session, bot))
    dp.include_router(start_router.router)
    dp.include_router(catalog_router.router)
    dp.include_router(cart_router.router)
    dp.include_router(order_router.router)
    dp.include_router(admin_router.router)
    dp.include_router(faq_router.router)

    await bot.set_my_commands(BOT_COMMANDS_PRIVATE, scope=BotCommandScopeAllPrivateChats())
    await bot.set_my_commands(BOT_COMMANDS_GROUP, scope=BotCommandScopeAllGroupChats())

    if config.webapp_url:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Открыть магазин",
                web_app=WebAppInfo(url=config.webapp_url),
            ),
        )
        logger.info("Menu button set to Web App: %s", config.webapp_url)

    if config.internal_url:
        asyncio.create_task(run_notify_server(bot, session_factory, port=config.notify_port))
    asyncio.create_task(run_broadcast_worker(bot, config, session_factory))

    try:
        logger.info("Bot starting polling")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
