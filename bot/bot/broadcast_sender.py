"""
Фоновый отправщик рассылок: по таймеру ищет рассылки со статусом ready,
отправляет пользователям, обновляет статус и счётчики.
"""
import asyncio
import logging
import re
from datetime import datetime, timezone

import aiohttp
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from bot.config import BotConfig
from bot.database import get_session
from bot.repositories import broadcast_repository as broadcast_repo

logger = logging.getLogger(__name__)

BROADCAST_CHECK_INTERVAL_SEC = 5

# Подпись к фото в Telegram — макс. 1024 символа (не как у обычного сообщения).
_MAX_PHOTO_CAPTION = 1024


def _truncate_caption(text: str) -> str:
    t = (text or "").strip()
    if len(t) <= _MAX_PHOTO_CAPTION:
        return t
    return t[: _MAX_PHOTO_CAPTION - 1] + "…"


def _strip_html_for_plain(text: str) -> str:
    """Грубое снятие тегов для запасной отправки без parse_mode."""
    s = re.sub(r"<[^>]+>", "", text or "")
    return s.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").strip()


async def _download_image_bytes(url: str) -> bytes | None:
    """
    Скачивание файла на стороне бота (а не URL в Telegram API).
    Нужно для ngrok free (интерстициальная HTML-страница для запросов без заголовка)
    и для стабильной доставки.
    """
    headers = {
        "User-Agent": "tg-shop-bot/broadcast",
        # ngrok free: без заголовка часто отдаётся HTML вместо картинки
        "ngrok-skip-browser-warning": "1",
    }
    timeout = aiohttp.ClientTimeout(total=90)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers, allow_redirects=True) as resp:
                if resp.status != 200:
                    logger.warning(
                        "Рассылка: скачивание картинки %s — HTTP %s", url, resp.status
                    )
                    return None
                ct = (resp.headers.get("Content-Type") or "").lower()
                if "text/html" in ct:
                    logger.warning(
                        "Рассылка: по URL пришёл HTML, не изображение (часто ngrok/warning): %s",
                        url,
                    )
                    return None
                data = await resp.read()
                if not data or len(data) < 32:
                    logger.warning("Рассылка: пустой или слишком короткий ответ: %s", url)
                    return None
                return data
    except Exception as e:
        logger.warning("Рассылка: ошибка скачивания %s: %s", url, e)
        return None


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

    photo_bytes: bytes | None = None
    if photo_url:
        photo_bytes = await _download_image_bytes(photo_url)
        if photo_bytes is None:
            logger.warning(
                "Рассылка #%s: не удалось скачать картинку, шлём только текст (%s)",
                broadcast.id,
                photo_url,
            )

    caption = _truncate_caption(broadcast.text or "")
    ext = "jpg"
    if broadcast.image:
        low = broadcast.image.lower()
        if low.endswith(".png"):
            ext = "png"
        elif low.endswith(".webp"):
            ext = "webp"
        elif low.endswith(".gif"):
            ext = "gif"

    for tid in telegram_ids:
        try:
            if photo_bytes is not None:
                # Новый объект на каждого пользователя (буфер одноразовый).
                photo_file = BufferedInputFile(photo_bytes, filename=f"broadcast.{ext}")
                try:
                    await bot.send_photo(
                        chat_id=tid,
                        photo=photo_file,
                        caption=caption or None,
                        parse_mode=ParseMode.HTML if caption else None,
                    )
                except TelegramBadRequest as e:
                    # Невалидный HTML в подписи — повтор без разметки
                    if caption and "parse" in str(e).lower():
                        photo_file_plain = BufferedInputFile(
                            photo_bytes, filename=f"broadcast.{ext}"
                        )
                        await bot.send_photo(
                            chat_id=tid,
                            photo=photo_file_plain,
                            caption=_truncate_caption(
                                _strip_html_for_plain(broadcast.text or "")
                            )
                            or None,
                        )
                    else:
                        raise
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
