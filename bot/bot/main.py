import asyncio
import logging
import logging.handlers
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BotConfig
from bot.database import create_session_factory, get_session
from bot.handlers import start as start_router
from bot.handlers import catalog as catalog_router
from bot.handlers import cart as cart_router
from bot.handlers import order as order_router
from bot.middlewares.config_middleware import ConfigMiddleware
from bot.middlewares.logging_middleware import LoggingMiddleware
from bot.middlewares.user_middleware import UserMiddleware
from bot.middlewares.subscription_middleware import SubscriptionMiddleware

_log_dir = Path(__file__).resolve().parent.parent / "logs"
_log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.handlers.RotatingFileHandler(
            _log_dir / "bot.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
        ),
    ],
)
logger = logging.getLogger(__name__)

BOT_COMMANDS = [
    BotCommand(command="start", description="Начать"),
    BotCommand(command="catalog", description="Каталог"),
    BotCommand(command="cart", description="Корзина"),
    BotCommand(command="help", description="Помощь"),
]


async def main() -> None:
    config = BotConfig.from_env()
    if not config.token:
        logger.error("BOT_TOKEN not set")
        return

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

    await bot.set_my_commands(BOT_COMMANDS)

    try:
        logger.info("Bot starting polling")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
