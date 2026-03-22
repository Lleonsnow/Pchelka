from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

from bot.database import get_session
from bot.repositories import faq_repository as faq_repo

router = Router(name="faq")

# Лимит текста сообщения при выборе статьи (Telegram Bot API).
_INLINE_MESSAGE_MAX = 4096


def _truncate(s: str, max_len: int) -> str:
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"


@router.inline_query()
async def inline_faq(inline_query: InlineQuery, session_factory) -> None:
    query = (inline_query.query or "").strip()
    async with get_session(session_factory) as session:
        if query:
            items = await faq_repo.search_faq(session, query, limit=15)
        else:
            items = await faq_repo.get_popular_faq(session, limit=10)
    if not items:
        if query:
            title = "Ничего не найдено"
            body = "По вашему запросу подходящих вопросов пока нет."
        else:
            title = "Пока нет вопросов"
            body = "Частые вопросы ещё не добавлены в админке."
        await inline_query.answer(
            [
                InlineQueryResultArticle(
                    id="faq_empty",
                    title=title,
                    input_message_content=InputTextMessageContent(message_text=body),
                )
            ],
            cache_time=60,
        )
        return
    results = [
        InlineQueryResultArticle(
            id=f"faq_{item.id}",
            title=_truncate(item.question, 64),
            description=_truncate(item.answer, 128) if item.answer else None,
            input_message_content=InputTextMessageContent(
                message_text=_truncate(item.answer, _INLINE_MESSAGE_MAX)
            ),
        )
        for item in items
    ]
    await inline_query.answer(results, cache_time=60)
