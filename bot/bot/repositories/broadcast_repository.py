from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


BROADCAST_STATUS_READY = "ready"
BROADCAST_STATUS_SENT = "sent"


@dataclass
class BroadcastData:
    id: int
    text: str
    image: str | None  # путь относительно media, например broadcasts/2025/03/xxx.jpg

    @classmethod
    def from_row(cls, row: Any) -> "BroadcastData":
        img = row.get("image")
        return cls(
            id=row["id"],
            text=row["text"] or "",
            image=str(img) if img else None,
        )


async def get_ready_broadcasts(session: AsyncSession) -> list[BroadcastData]:
    """Список рассылок со статусом ready."""
    result = await session.execute(
        text("""
            SELECT id, text, image
            FROM broadcasts_broadcast
            WHERE status = :status
            ORDER BY id
        """),
        {"status": BROADCAST_STATUS_READY},
    )
    return [BroadcastData.from_row(row) for row in result.mappings()]


async def get_all_telegram_ids(session: AsyncSession) -> list[int]:
    """Все telegram_id пользователей для рассылки."""
    result = await session.execute(
        text("SELECT telegram_id FROM users_telegramuser")
    )
    return [row[0] for row in result.fetchall()]


async def set_broadcast_sent(
    session: AsyncSession,
    broadcast_id: int,
    delivered_count: int,
    error_count: int,
    sent_at: datetime,
) -> None:
    """Обновить рассылку после отправки."""
    await session.execute(
        text("""
            UPDATE broadcasts_broadcast
            SET status = :status, delivered_count = :delivered, error_count = :errors, sent_at = :sent_at
            WHERE id = :id
        """),
        {
            "id": broadcast_id,
            "status": BROADCAST_STATUS_SENT,
            "delivered": delivered_count,
            "errors": error_count,
            "sent_at": sent_at,
        },
    )
