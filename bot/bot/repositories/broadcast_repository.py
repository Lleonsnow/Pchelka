from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


BROADCAST_STATUS_READY = "ready"
BROADCAST_STATUS_SENT = "sent"


@dataclass
class BroadcastTemplateRow:
    id: int
    name: str
    text: str
    image: str | None

    @classmethod
    def from_row(cls, row: Any) -> "BroadcastTemplateRow":
        img = row.get("image")
        return cls(
            id=row["id"],
            name=row["name"] or "",
            text=row["text"] or "",
            image=str(img) if img else None,
        )


@dataclass
class BroadcastHistoryRow:
    id: int
    status: str
    text_preview: str
    delivered_count: int
    error_count: int
    created_at: datetime | None

    @classmethod
    def from_row(cls, row: Any) -> "BroadcastHistoryRow":
        return cls(
            id=row["id"],
            status=row["status"] or "",
            text_preview=(row.get("text_preview") or "")[:200],
            delivered_count=int(row.get("delivered_count") or 0),
            error_count=int(row.get("error_count") or 0),
            created_at=row.get("created_at"),
        )


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


async def list_broadcast_templates(session: AsyncSession, limit: int = 30) -> list[BroadcastTemplateRow]:
    result = await session.execute(
        text("""
            SELECT id, name, text, image
            FROM broadcasts_broadcasttemplate
            WHERE is_active = true
            ORDER BY "order", id
            LIMIT :limit
        """),
        {"limit": limit},
    )
    return [BroadcastTemplateRow.from_row(row) for row in result.mappings()]


async def enqueue_broadcast_from_template(session: AsyncSession, template_id: int) -> int | None:
    """INSERT в broadcasts_broadcast из шаблона; None если шаблон не найден или неактивен."""
    result = await session.execute(
        text("""
            INSERT INTO broadcasts_broadcast (
                text, image, status, delivered_count, error_count, sent_at, created_at
            )
            SELECT t.text, t.image, :ready, 0, 0, NULL, NOW()
            FROM broadcasts_broadcasttemplate t
            WHERE t.id = :tid AND t.is_active = true
            RETURNING id
        """),
        {"tid": template_id, "ready": BROADCAST_STATUS_READY},
    )
    row = result.mappings().first()
    return int(row["id"]) if row else None


async def list_broadcast_history(session: AsyncSession, limit: int = 12) -> list[BroadcastHistoryRow]:
    result = await session.execute(
        text("""
            SELECT b.id, b.status,
                   LEFT(b."text", 120) AS text_preview,
                   b.delivered_count, b.error_count, b.created_at
            FROM broadcasts_broadcast b
            ORDER BY b.created_at DESC
            LIMIT :limit
        """),
        {"limit": limit},
    )
    return [BroadcastHistoryRow.from_row(row) for row in result.mappings()]


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
