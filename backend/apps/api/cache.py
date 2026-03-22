"""Кеш для GET-эндпоинтов WebApp API (каталог, FAQ, конфиг). Инвалидация — см. apps.catalog.signals / apps.faq.signals."""

from __future__ import annotations

import hashlib

from django.core.cache import cache

# Версия в ключе: bump при изменении каталога/FAQ в админке
_PUBLIC_VERSION_KEY = "api:webapp_public_v"
# Запасной TTL, если сигнал не сработал
PUBLIC_CACHE_TTL = 120
CONFIG_CACHE_TTL = 300


def public_cache_version() -> int:
    return int(cache.get(_PUBLIC_VERSION_KEY) or 0)


def bump_public_api_cache() -> None:
    """Сбросить кеш публичных ответов API (товары, категории, FAQ)."""
    try:
        cache.incr(_PUBLIC_VERSION_KEY)
    except ValueError:
        cache.set(_PUBLIC_VERSION_KEY, 1, timeout=None)


def cache_get_json(key: str):
    return cache.get(key)


def cache_set_json(key: str, data, timeout: int = PUBLIC_CACHE_TTL) -> None:
    cache.set(key, data, timeout)


def key_categories(parent_param: str, v: int) -> str:
    return f"api:categories:{parent_param}:v{v}"


def key_products_list(host: str, category_id: str, search: str, v: int) -> str:
    sh = hashlib.sha256(search.encode("utf-8")).hexdigest()[:20]
    return f"api:products:{host}:{category_id or '-'}:{sh}:v{v}"


def key_product_detail(host: str, pk: int, v: int) -> str:
    return f"api:product:{host}:{pk}:v{v}"


def key_faq(v: int) -> str:
    return f"api:faq:v{v}"


WEBAPP_CONFIG_CACHE_KEY = "api:webapp_config:v1"

__all__ = [
    "CONFIG_CACHE_TTL",
    "PUBLIC_CACHE_TTL",
    "WEBAPP_CONFIG_CACHE_KEY",
    "bump_public_api_cache",
    "cache_get_json",
    "cache_set_json",
    "key_categories",
    "key_faq",
    "key_product_detail",
    "key_products_list",
    "public_cache_version",
]
