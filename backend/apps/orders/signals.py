import json
import logging
import urllib.request
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.orders.models import Order

logger = logging.getLogger(__name__)


def notify_bot_admin_new_order(order_id: int) -> None:
    """Хук бота: новый заказ из Django (WebApp) → то же уведомление в admin_chat, что при заказе из бота."""
    url = (getattr(settings, "BOT_INTERNAL_URL", None) or "").strip().rstrip("/")
    if not url:
        return
    url = url + "/notify"
    try:
        data = json.dumps({"order_id": order_id, "event": "admin_new_order"}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        logger.warning("Bot admin_new_order hook failed: %s", e)


@receiver(post_save, sender=Order)
def order_status_changed(sender, instance: Order, created: bool, **kwargs) -> None:
    """При сохранении заказа (в т.ч. смене статуса в админке) дергаем хук бота для уведомления пользователя."""
    if created:
        return
    url = (getattr(settings, "BOT_INTERNAL_URL", None) or "").strip().rstrip("/")
    if not url:
        return
    url = url + "/notify"
    try:
        data = json.dumps({"order_id": instance.id, "status": instance.status}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        logger.warning("Order notify hook failed: %s", e)
