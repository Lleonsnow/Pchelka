from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Загружаем .env из корня проекта (tg-shop/.env)
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)


class BotConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_env_path) if _env_path.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    BOT_TOKEN: str = Field(..., description="Токен бота от BotFather")
    DATABASE_URL: str = Field(..., description="URL PostgreSQL")
    BOT_INTERNAL_URL: str | None = Field(default=None, description="URL бота для хуков (Django -> /notify)")
    BOT_NOTIFY_PORT: int = Field(default=8080, description="Порт aiohttp для /notify")
    MEDIA_BASE_URL: str = Field(..., description="Базовый URL медиа (фото товаров), без слэша в конце")
    TELEGRAM_WEBAPP_HOST: str = Field(default="", description="URL WebApp (Mini App) для кнопки меню и открытия каталога")
    TELEGRAM_BOT_USERNAME: str = Field(default="", description="Username без @ — ссылки t.me в клавиатурах")
    TELEGRAM_MINIAPP_SHORT_NAME: str = Field(default="", description="Direct Link в BotFather → t.me/bot/SHORT")
    MEDIA_FETCH_BASE_URL: str = Field(
        default="",
        description="Скачивание файлов рассылки ботом; пусто = MEDIA_BASE_URL. В Docker: http://backend:8000",
    )

    @property
    def token(self) -> str:
        return self.BOT_TOKEN

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL

    @property
    def internal_url(self) -> str | None:
        return self.BOT_INTERNAL_URL or None

    @property
    def media_base_url(self) -> str:
        return (self.MEDIA_BASE_URL or "").strip().rstrip("/")

    @property
    def notify_port(self) -> int:
        return self.BOT_NOTIFY_PORT

    @property
    def webapp_url(self) -> str:
        return (self.TELEGRAM_WEBAPP_HOST or "").strip().rstrip("/")

    @property
    def media_download_base_url(self) -> str:
        """База для HTTP-скачивания медиа контейнером бота (рассылки)."""
        internal = (self.MEDIA_FETCH_BASE_URL or "").strip().rstrip("/")
        if internal:
            return internal
        return self.media_base_url
