"""Минимальный aiohttp-сервер для приёма хуков от Django: смена статуса заказа, новый заказ из WebApp."""
import json
import logging

from aiohttp import web

from bot.handlers.admin import notify_admin_new_order, notify_user_order_status

logger = logging.getLogger(__name__)


async def handle_notify(request: web.Request) -> web.Response:
    """POST /notify: {"order_id", "status"} — пользователю; {"order_id", "event": "admin_new_order"} — админ-чат."""
    if request.method != "POST":
        return web.Response(status=405)
    try:
        body = await request.json()
    except Exception as e:
        logger.warning("notify: invalid json %s", e)
        return web.Response(status=400, text="Invalid JSON")
    order_id = body.get("order_id")
    if body.get("event") == "admin_new_order":
        if order_id is None:
            return web.Response(status=400, text="Missing order_id")
        try:
            order_id = int(order_id)
        except (TypeError, ValueError):
            return web.Response(status=400, text="order_id must be int")
        bot = request.app.get("bot")
        session_factory = request.app.get("session_factory")
        if not bot or not session_factory:
            return web.Response(status=503, text="Bot not ready")
        try:
            await notify_admin_new_order(bot, session_factory, order_id)
        except Exception as e:
            logger.exception("notify admin_new_order: %s", e)
            return web.Response(status=500, text="Notify failed")
        return web.Response(status=200, text="OK")
    status = body.get("status")
    if order_id is None or not status:
        return web.Response(status=400, text="Missing order_id or status")
    try:
        order_id = int(order_id)
    except (TypeError, ValueError):
        return web.Response(status=400, text="order_id must be int")
    bot = request.app.get("bot")
    session_factory = request.app.get("session_factory")
    if not bot or not session_factory:
        return web.Response(status=503, text="Bot not ready")
    try:
        await notify_user_order_status(bot, session_factory, order_id, str(status))
    except Exception as e:
        logger.exception("notify: %s", e)
        return web.Response(status=500, text="Notify failed")
    return web.Response(status=200, text="OK")


def create_app(bot, session_factory) -> web.Application:
    app = web.Application()
    app["bot"] = bot
    app["session_factory"] = session_factory
    app.router.add_post("/notify", handle_notify)
    return app


async def run_notify_server(bot, session_factory, host: str = "0.0.0.0", port: int = 8080) -> None:
    app = create_app(bot, session_factory)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info("Notify server listening on %s:%s", host, port)
