"""
Фоновый отправщик рассылок: по таймеру ищет рассылки со статусом ready,
отправляет пользователям, обновляет статус и счётчики.
"""
import asyncio
import logging
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.enums import ParseMode
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from bot.config import BotConfig
from bot.database import get_session
from bot.repositories import broadcast_repository as broadcast_repo

logger = logging.getLogger(__name__)

BROADCAST_CHECK_INTERVAL_SEC = 45


async def _send_one_broadcast(
    bot: Bot,
    config: BotConfig,
    session_factory: async_sessionmaker[AsyncSession],
    broadcast: broadcast_repo.BroadcastData,
) -> None:
    async with get_session(session_factory) as session:
        telegram_ids = await broadcast_repo.get_all_telegram_ids(session)
    if not telegram_ids:
        async with get_session(session_factory) as session:
            await broadcast_repo.set_broadcast_sent(
                session, broadcast.id, 0, 0, datetime.now(timezone.utc)
            )
        return

    delivered = 0
    errors = 0
    photo_url = None
    if broadcast.image:
        base = config.media_base_url.rstrip("/")
        path = broadcast.image.lstrip("/")
        photo_url = f"{base}/media/{path}"

    for tid in telegram_ids:
        try:
            if photo_url:
                await bot.send_photo(
                    chat_id=tid,
                    photo=photo_url,
                    caption=broadcast.text,
                    parse_mode=ParseMode.HTML,
                )
            else:
                await bot.send_message(
                    chat_id=tid,
                    text=broadcast.text,
                    parse_mode=ParseMode.HTML,
                )
            delivered += 1
        except Exception as e:
            logger.warning("Broadcast %s to %s: %s", broadcast.id, tid, e)
            errors += 1
        await asyncio.sleep(0.05)

    async with get_session(session_factory) as session:
        await broadcast_repo.set_broadcast_sent(
            session, broadcast.id, delivered, errors, datetime.now(timezone.utc)
        )
    logger.info("Broadcast #%s sent: delivered=%s errors=%s", broadcast.id, delivered, errors)


async def run_broadcast_worker(
    bot: Bot,
    config: BotConfig,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Запускает цикл проверки готовых рассылок."""
    while True:
        try:
            await asyncio.sleep(BROADCAST_CHECK_INTERVAL_SEC)
            async with get_session(session_factory) as session:
                ready = await broadcast_repo.get_ready_broadcasts(session)
            for broadcast in ready:
                try:
                    await _send_one_broadcast(bot, config, session_factory, broadcast)
                except Exception as e:
                    logger.exception("Broadcast #%s failed: %s", broadcast.id, e)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.exception("Broadcast worker error: %s", e)
