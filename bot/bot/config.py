import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class BotConfig:
    token: str
    database_url: str
    internal_url: str | None  # для приёма хуков от Django
    media_base_url: str  # базовый URL медиа (фото товаров), без слэша в конце

    @classmethod
    def from_env(cls) -> "BotConfig":
        token = os.environ.get("BOT_TOKEN", "")
        database_url = os.environ.get(
            "DATABASE_URL",
            "postgres://tgshop:tgshop@localhost:5432/tgshop",
        )
        internal_url = os.environ.get("BOT_INTERNAL_URL") or None
        media_base_url = (
            os.environ.get("MEDIA_BASE_URL") or "http://localhost:8000/media"
        ).rstrip("/")
        return cls(
            token=token,
            database_url=database_url,
            internal_url=internal_url,
            media_base_url=media_base_url,
        )
