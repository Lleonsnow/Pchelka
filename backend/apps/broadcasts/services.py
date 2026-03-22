"""Очередь рассылок из шаблона (статус ready — забирает бот)."""

from __future__ import annotations

from django.db import transaction

from .models import Broadcast, BroadcastTemplate


@transaction.atomic
def queue_broadcast_from_template(template: BroadcastTemplate) -> Broadcast:
    """
    Создаёт запись рассылки со статусом «Готово» — копирует текст и ссылку на тот же файл картинки.
    """
    broadcast = Broadcast.objects.create(
        text=template.text,
        status=Broadcast.Status.READY,
    )
    if template.image:
        broadcast.image = template.image
        broadcast.save(update_fields=["image"])
    return broadcast
