from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class UserData:
    id: int
    telegram_id: int
    username: str
    first_name: str
    last_name: str
    phone: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: Any) -> "UserData":
        return cls(
            id=row["id"],
            telegram_id=row["telegram_id"],
            username=row["username"] or "",
            first_name=row["first_name"] or "",
            last_name=row["last_name"] or "",
            phone=row["phone"] or "",
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str = "",
    first_name: str = "",
    last_name: str = "",
) -> UserData:
    """Возвращает пользователя по telegram_id; создаёт запись, если нет."""
    result = await session.execute(
        text("""
            SELECT id, telegram_id, username, first_name, last_name, phone, created_at, updated_at
            FROM users_telegramuser WHERE telegram_id = :tid
        """),
        {"tid": telegram_id},
    )
    row = result.mappings().first()
    if row:
        await session.execute(
            text("""
                UPDATE users_telegramuser
                SET username = :username, first_name = :first_name, last_name = :last_name, updated_at = NOW()
                WHERE telegram_id = :tid
            """),
            {
                "tid": telegram_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
            },
        )
        result = await session.execute(
            text("""
                SELECT id, telegram_id, username, first_name, last_name, phone, created_at, updated_at
                FROM users_telegramuser WHERE telegram_id = :tid
            """),
            {"tid": telegram_id},
        )
        row = result.mappings().first()
        return UserData.from_row(row)

    await session.execute(
        text("""
            INSERT INTO users_telegramuser (telegram_id, username, first_name, last_name, phone, created_at, updated_at)
            VALUES (:tid, :username, :first_name, :last_name, '', NOW(), NOW())
        """),
        {
            "tid": telegram_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
        },
    )
    result = await session.execute(
        text("""
            SELECT id, telegram_id, username, first_name, last_name, phone, created_at, updated_at
            FROM users_telegramuser WHERE telegram_id = :tid
        """),
        {"tid": telegram_id},
    )
    row = result.mappings().first()
    return UserData.from_row(row)


async def update_user_phone(session: AsyncSession, telegram_id: int, phone: str) -> None:
    await session.execute(
        text("""
            UPDATE users_telegramuser SET phone = :phone, updated_at = NOW() WHERE telegram_id = :tid
        """),
        {"tid": telegram_id, "phone": phone},
    )
