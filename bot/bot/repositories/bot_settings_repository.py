from dataclasses import dataclass
from time import monotonic

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class BotSettingsData:
    admin_chat_id: int | None
    admin_telegram_ids: list[int]


@dataclass
class SubscriptionChannelData:
    channel_id: int
    title: str
    invite_link: str


_CACHE_TTL = 60.0  # секунд
_bot_settings_cache: tuple[float, BotSettingsData | None] = (0.0, None)
_channels_cache: tuple[float, list[SubscriptionChannelData]] = (0.0, [])


def _now() -> float:
    return monotonic()


async def get_bot_settings(session: AsyncSession) -> BotSettingsData | None:
    result = await session.execute(
        text("""
            SELECT admin_chat_id, admin_telegram_ids
            FROM bot_settings_botsettings LIMIT 1
        """)
    )
    row = result.mappings().first()
    if not row:
        return None
    ids = row["admin_telegram_ids"] or []
    if not isinstance(ids, list):
        ids = []
    return BotSettingsData(
        admin_chat_id=row["admin_chat_id"],
        admin_telegram_ids=[int(x) for x in ids if isinstance(x, (int, str)) and str(x).isdigit()],
    )


async def get_subscription_channels(session: AsyncSession) -> list[SubscriptionChannelData]:
    result = await session.execute(
        text("""
            SELECT channel_id, title, invite_link
            FROM bot_settings_subscriptionchannel
            ORDER BY "order", channel_id
        """)
    )
    return [
        SubscriptionChannelData(
            channel_id=row["channel_id"],
            title=row["title"] or f"Канал {row['channel_id']}",
            invite_link=row["invite_link"] or "",
        )
        for row in result.mappings()
    ]


async def get_bot_settings_cached(session_factory, get_session) -> BotSettingsData | None:
    global _bot_settings_cache
    now = _now()
    if now - _bot_settings_cache[0] < _CACHE_TTL and _bot_settings_cache[1] is not None:
        return _bot_settings_cache[1]
    async with get_session(session_factory) as session:
        data = await get_bot_settings(session)
    _bot_settings_cache = (now, data)
    return data


async def get_subscription_channels_cached(session_factory, get_session) -> list[SubscriptionChannelData]:
    global _channels_cache
    now = _now()
    if now - _channels_cache[0] < _CACHE_TTL:
        return _channels_cache[1]
    async with get_session(session_factory) as session:
        channels = await get_subscription_channels(session)
    _channels_cache = (now, channels)
    return channels
