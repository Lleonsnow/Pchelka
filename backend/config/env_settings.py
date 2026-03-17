"""Настройки из env через Pydantic. Все секреты и URL только из переменных окружения."""
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# .env в корне проекта (tg-shop/.env)
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_env_path) if _env_path.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # PostgreSQL
    POSTGRES_DB: str = Field(..., description="Имя БД PostgreSQL")
    POSTGRES_USER: str = Field(..., description="Пользователь PostgreSQL")
    POSTGRES_PASSWORD: str = Field(..., description="Пароль PostgreSQL")
    POSTGRES_HOST: str = Field(default="localhost", description="Хост PostgreSQL (db в Docker)")
    POSTGRES_PORT: str = Field(default="5432", description="Порт PostgreSQL")

    # Django
    SECRET_KEY: str = Field(..., description="Django SECRET_KEY")
    DEBUG: bool = Field(..., description="Django DEBUG")
    ALLOWED_HOSTS: str = Field(..., description="Разделённый запятыми список хостов")

    # Опционально
    BOT_INTERNAL_URL: str = Field(default="", description="URL бота для хука уведомлений")
    BOT_TOKEN: str = Field(default="", description="Токен бота для валидации initData WebApp")
    TELEGRAM_WEBAPP_HOST: str = Field(default="", description="Origin WebApp для CORS (например https://xxx.ngrok.io)")
    DEV_WEBAPP_TELEGRAM_ID: str = Field(default="", description="При DEBUG: telegram_id для запросов без initData (тест в браузере)")

    @property
    def database_url(self) -> str:
        return (
            f"postgres://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def allowed_hosts_list(self) -> list[str]:
        return [x.strip() for x in self.ALLOWED_HOSTS.split(",") if x.strip()]
