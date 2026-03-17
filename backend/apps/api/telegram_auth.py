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
    или None при неверной подписи. При неудаче причина доступна через
    validate_init_data_reason() если нужна отладка.
    """
    result, _ = _validate_init_data_with_reason(init_data_raw, bot_token)
    return result


_last_failure_reason: str | None = None


def _validate_init_data_with_reason(
    init_data_raw: str, bot_token: str
) -> tuple[dict[str, Any] | None, str | None]:
    """Валидация initData с возвратом причины при отказе (для логов)."""
    global _last_failure_reason
    _last_failure_reason = None
    if not init_data_raw or not bot_token:
        _last_failure_reason = "empty_data_or_token"
        return (None, _last_failure_reason)
    try:
        bot_token = bot_token.strip()
        init_data_raw = init_data_raw.strip().replace(" ", "+")
        # Парсим как в эталоне: декодируем значения, data-check-string — из декодированных пар
        received_hash = ""
        params_dict = {}
        for part in init_data_raw.split("&"):
            if "=" not in part:
                continue
            key, _, value = part.partition("=")
            key = key.strip()
            if key == "hash":
                received_hash = value
                continue
            params_dict[key] = urllib.parse.unquote(value)
        if not received_hash:
            _last_failure_reason = "missing_hash"
            return (None, _last_failure_reason)
        data_check_string = "\n".join(
            f"{k}={params_dict[k]}" for k in sorted(params_dict.keys())
        )
        # secret_key = HMAC(key="WebAppData", message=bot_token) — порядок по доке Telegram
        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode(),
            hashlib.sha256,
        ).digest()
        computed_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(computed_hash, received_hash):
            _last_failure_reason = "hash_mismatch"
            return (None, _last_failure_reason)
        auth_date = params_dict.get("auth_date")
        if auth_date:
            try:
                from time import time
                now = int(time())
                ad = int(auth_date)
                if abs(ad - now) > 86400:
                    _last_failure_reason = f"auth_date_expired (auth_date={ad}, now={now}, diff_sec={abs(ad - now)})"
                    return (None, _last_failure_reason)
            except (ValueError, TypeError):
                _last_failure_reason = "auth_date_invalid"
                return (None, _last_failure_reason)
        return (params_dict, None)
    except Exception as e:
        _last_failure_reason = f"exception: {type(e).__name__}"
        return (None, _last_failure_reason)


def get_validation_failure_reason() -> str | None:
    """Причина последнего отказа validate_init_data (для отладки)."""
    return _last_failure_reason


def get_telegram_user_from_validated(validated: dict[str, Any]) -> dict[str, Any] | None:
    """Из валидированного initData извлекает объект user (JSON)."""
    user_str = validated.get("user")
    if not user_str:
        return None
    try:
        return json.loads(user_str)
    except (json.JSONDecodeError, TypeError):
        return None
