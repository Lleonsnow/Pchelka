from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

from bot.database import get_session
from bot.repositories import faq_repository as faq_repo

router = Router(name="faq")


@router.inline_query()
async def inline_faq(inline_query: InlineQuery, session_factory) -> None:
    query = (inline_query.query or "").strip()
    async with get_session(session_factory) as session:
        if query:
            items = await faq_repo.search_faq(session, query, limit=15)
        else:
            items = await faq_repo.get_popular_faq(session, limit=10)
    if not items:
        await inline_query.answer(
            [InlineQueryResultArticle(
                id="faq_empty",
                title="Ничего не найдено",
                input_message_content=InputTextMessageContent(message_text="По вашему запросу вопросов пока нет."),
            )],
            cache_time=60,
        )
        return
    results = [
        InlineQueryResultArticle(
            id=f"faq_{item.id}",
            title=item.question[:64] + ("..." if len(item.question) > 64 else ""),
            description=(item.answer[:128] + "...") if len(item.answer) > 128 else item.answer,
            input_message_content=InputTextMessageContent(message_text=item.answer),
        )
        for item in items
    ]
    await inline_query.answer(results, cache_time=60)
