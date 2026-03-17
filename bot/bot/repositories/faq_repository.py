from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class FAQData:
    id: int
    question: str
    answer: str

    @classmethod
    def from_row(cls, row: Any) -> "FAQData":
        return cls(
            id=row["id"],
            question=row["question"] or "",
            answer=row["answer"] or "",
        )


async def search_faq(session: AsyncSession, query: str, limit: int = 15) -> list[FAQData]:
    """Поиск по вопросу и ответу. Пустая строка — не ищем."""
    q = (query or "").strip().lower()
    if not q:
        return []
    pattern = f"%{q}%"
    result = await session.execute(
        text("""
            SELECT id, question, answer
            FROM faq_faq
            WHERE is_active = true
              AND (LOWER(question) LIKE :p OR LOWER(answer) LIKE :p)
            ORDER BY "order", id
            LIMIT :limit
        """),
        {"p": pattern, "limit": limit},
    )
    return [FAQData.from_row(row) for row in result.mappings()]


async def get_popular_faq(session: AsyncSession, limit: int = 10) -> list[FAQData]:
    """Популярные (первые N по order) для пустого запроса."""
    result = await session.execute(
        text("""
            SELECT id, question, answer
            FROM faq_faq
            WHERE is_active = true
            ORDER BY "order", id
            LIMIT :limit
        """),
        {"limit": limit},
    )
    return [FAQData.from_row(row) for row in result.mappings()]
