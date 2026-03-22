# Telegram Shop

Магазин внутри Telegram: **бот** (Aiogram 3), **бэкенд** (Django + DRF + админка), **мини-приложение** (Next.js). Бот и Django используют **одну PostgreSQL**.

## Возможности

- **WebApp (Next.js):** каталог с категориями и поиском, карточка товара, корзина, оформление заказа, список заказов в профиле, FAQ на главной; авторизация API по заголовку `X-Telegram-Init-Data`.
- **Бот (Aiogram):** старт, каталог и корзина в чате, FSM оформления заказа, FAQ, админ-команды (в т.ч. привязка админ-чата, рассылки), HTTP-сервер `/notify` для вызовов из Django.
- **Django:** REST API под префиксом `/api/webapp/` (см. `backend/apps/api/urls.py`), модели каталога, корзины, заказов, пользователей Telegram, FAQ, рассылок, настроек бота; кастомизация админки (шаблоны в `backend/templates/admin/`).
- **Уведомления:** новый заказ из WebApp → админ-чат; смена статуса заказа в админке → пользователю (через `BOT_INTERNAL_URL` → бот).
- **Prod:** `docker-compose.prod.yml` — nginx с TLS (Let’s Encrypt: том `./ssl`, webroot `./certbot-webroot`, образ `nginx/` + шаблон `nginx.prod.conf.template`), скрипты `scripts/certbot-standalone.sh` и `scripts/certbot-webroot.sh`.

## Быстрый старт

1. Скопируйте `.env.example` в `.env` и задайте как минимум: `POSTGRES_PASSWORD`, `SECRET_KEY`, `BOT_TOKEN` (остальное — по комментариям в `.env.example`).

2. Запуск всех сервисов (БД, backend, bot, webapp, nginx):

```bash
docker compose up --build
```

3. Первый вход в админку — создайте суперпользователя:

```bash
docker compose exec backend python manage.py createsuperuser
```

4. Тестовые данные (категории, товары, тестовые фото товаров, FAQ, шаблоны рассылок):

```bash
docker compose exec backend python manage.py seed
```

Полный сброс каталога и связанных данных, затем повторная загрузка сидера (нужен уже запущенный `docker compose up`, без `run --rm`):

```bash
docker compose exec backend python manage.py seed --clear
```

Повторный `seed` без `--clear` добавляет только отсутствующие записи и фото там, где их ещё нет. С `--clear` сначала удаляются заказы, категории, товары (и их файлы в БД каскадом), FAQ, шаблоны рассылок и журнал рассылок; настройки бота не трогаются.

## Куда заходить после запуска

| Сервис | URL | Назначение |
|--------|-----|------------|
| **nginx** | http://localhost (порт из `NGINX_PORT`, по умолчанию 80) | Единая точка входа: WebApp, `/api/`, `/admin/`, `/media/` |
| Backend напрямую | http://localhost:8000 | Разработка API и админки без прокси |
| WebApp (dev) | http://localhost:3000 | Next.js с HMR; API при порте 3000 уходит на `localhost:8000` (см. `webapp/src/lib/api.ts`) |

Для Telegram Mini App нужен **публичный HTTPS** на nginx (например `ngrok http 80`). В `.env` укажите `TELEGRAM_WEBAPP_HOST=https://....` и добавьте хост в `ALLOWED_HOSTS`.

## Структура репозитория

```
tg-shop/
├── backend/          # Django: config/, apps (api, catalog, cart, orders, users, faq, broadcasts, bot_settings)
├── bot/              # Aiogram: handlers, keyboards, middlewares, repositories, notify_server
├── webapp/           # Next.js: app router, components, lib/api.ts, lib/telegram.ts
├── nginx/            # Обратный прокси (конфиг в nginx/)
├── docs/             # ARCHITECTURE*, SECURITY, TESTING, PLAN, чеклисты, BOT_GROUP_PRIVACY
├── docker-compose.yml
└── docker-compose.prod.yml
```

## Важные переменные окружения

| Переменная | Зачем |
|------------|--------|
| `POSTGRES_*`, `SECRET_KEY`, `ALLOWED_HOSTS` | БД и базовые настройки Django. |
| `BOT_TOKEN` | Токен бота; в Django читается в `TELEGRAM_BOT_TOKEN` (см. `backend/config/settings.py`). |
| `DATABASE_URL` | Строка подключения к PostgreSQL (Docker подставляет из compose). |
| `TELEGRAM_WEBAPP_HOST` | Публичный URL мини-приложения (кнопка меню, CORS/CSRF). |
| `BOT_INTERNAL_URL` | В Docker обычно `http://bot:8080` — уведомления пользователю и админ-чату. |
| `MEDIA_BASE_URL` | Базовый URL бэкенда для медиа в боте (см. `.env.example`). |
| `NEXT_PUBLIC_API_URL` | Оставьте пустым за nginx; для dev без прокси: `http://localhost:8000`. |
| `TELEGRAM_BOT_USERNAME` | Username **без @**; в шаринге и `/api/webapp/config/`. |
| `TELEGRAM_MINIAPP_SHORT_NAME` | Short name Mini App в @BotFather (Bot → Mini Apps) — **второй сегмент** `t.me/bot/SHORT?startapp=…`. Часто **не равен** username; если пусто, шаринг использует `t.me/bot?start=product_<id>` (чат с ботом, карточка товара). |
| `DEV_WEBAPP_TELEGRAM_ID` | Только при `DEBUG`: WebApp в браузере без `initData`. |

Полный список и комментарии — в `.env.example`.