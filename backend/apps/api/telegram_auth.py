"""
Валидация initData от Telegram WebApp.
https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
"""
import hashlib
import hmac
import json
import urllib.parse
from typing import Any


def validate_init_data(init_data_raw: str, bot_token: str) -> dict[str, Any] | None:
    """
    Проверяет подпись initData и возвращает распарсенные параметры (включая user)
    или None при неверной подписи.
    """
    if not init_data_raw or not bot_token:
        return None
    try:
        params = urllib.parse.parse_qsl(init_data_raw, keep_blank_values=True)
        params_dict = dict(params)
        received_hash = params_dict.pop("hash", None)
        if not received_hash:
            return None
        # Data-check-string: пары key=value, отсортированные по key, разделитель \n
        data_check_pairs = sorted(params_dict.items())
        data_check_string = "\n".join(f"{k}={v}" for k, v in data_check_pairs)
        # secret_key = HMAC_SHA256(bot_token, "WebAppData")
        secret_key = hmac.new(
            bot_token.encode(),
            b"WebAppData",
            hashlib.sha256,
        ).digest()
        computed_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(computed_hash, received_hash):
            return None
        # Опционально: проверить auth_date (не старше 1 часа)
        auth_date = params_dict.get("auth_date")
        if auth_date:
            try:
                from time import time
                if abs(int(auth_date) - int(time())) > 3600:
                    return None
            except (ValueError, TypeError):
                return None
        return params_dict
    except Exception:
        return None


def get_telegram_user_from_validated(validated: dict[str, Any]) -> dict[str, Any] | None:
    """Из валидированного initData извлекает объект user (JSON)."""
    user_str = validated.get("user")
    if not user_str:
        return None
    try:
        return json.loads(user_str)
    except (json.JSONDecodeError, TypeError):
        return None
