from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories.cart_repository import get_cart_items, clear_cart

ORDER_STATUS_NEW = "new"
ORDER_STATUS_CONFIRMED = "confirmed"
ORDER_STATUS_PAYMENT_PENDING = "payment_pending"
ORDER_STATUS_PAID = "paid"
ORDER_STATUS_SHIPPED = "shipped"
ORDER_STATUS_DELIVERED = "delivered"
ORDER_STATUS_CANCELLED = "cancelled"

ORDER_STATUS_LABELS = {
    ORDER_STATUS_NEW: "Новый",
    ORDER_STATUS_CONFIRMED: "Подтверждён",
    ORDER_STATUS_PAYMENT_PENDING: "Ожидает оплаты",
    ORDER_STATUS_PAID: "Оплачен",
    ORDER_STATUS_SHIPPED: "Отправлен",
    ORDER_STATUS_DELIVERED: "Доставлен",
    ORDER_STATUS_CANCELLED: "Отменён",
}


async def create_order_from_cart(
    session: AsyncSession,
    user_id: int,
    full_name: str,
    address: str,
    phone: str,
) -> int | None:
    """
    Создаёт заказ из текущей корзины, очищает корзину.
    Возвращает order_id или None если корзина пуста.
    """
    items = await get_cart_items(session, user_id)
    if not items:
        return None
    total = sum(i.subtotal for i in items)
    result = await session.execute(
        text("""
            INSERT INTO orders_order (user_id, status, full_name, address, phone, total, created_at, updated_at)
            VALUES (:uid, :status, :full_name, :address, :phone, :total, NOW(), NOW())
            RETURNING id
        """),
        {
            "uid": user_id,
            "status": ORDER_STATUS_PAYMENT_PENDING,
            "full_name": full_name,
            "address": address,
            "phone": phone,
            "total": total,
        },
    )
    order_id = result.mappings().first()["id"]
    for item in items:
        await session.execute(
            text("""
                INSERT INTO orders_orderitem (order_id, product_id, quantity, price)
                VALUES (:oid, :pid, :qty, :price)
            """),
            {
                "oid": order_id,
                "pid": item.product_id,
                "qty": item.quantity,
                "price": item.price,
            },
        )
    await clear_cart(session, user_id)
    return order_id


async def get_order(session: AsyncSession, order_id: int, user_id: int) -> dict | None:
    """Получить заказ по id (если он принадлежит user_id)."""
    result = await session.execute(
        text("""
            SELECT id, status, full_name, address, phone, total, created_at
            FROM orders_order
            WHERE id = :oid AND user_id = :uid
        """),
        {"oid": order_id, "uid": user_id},
    )
    return dict(result.mappings().first()) if result.mappings().first() else None


async def set_order_status(
    session: AsyncSession,
    order_id: int,
    status: str,
) -> bool:
    """Обновить статус заказа. Возвращает True если заказ найден."""
    result = await session.execute(
        text("""
            UPDATE orders_order SET status = :status, updated_at = NOW()
            WHERE id = :oid
        """),
        {"oid": order_id, "status": status},
    )
    return result.rowcount > 0


async def get_order_user_telegram_id(session: AsyncSession, order_id: int) -> int | None:
    """Telegram ID пользователя заказа (для уведомлений)."""
    result = await session.execute(
        text("""
            SELECT u.telegram_id FROM orders_order o
            JOIN users_telegramuser u ON u.id = o.user_id
            WHERE o.id = :oid
        """),
        {"oid": order_id},
    )
    row = result.mappings().first()
    return row["telegram_id"] if row else None


async def get_order_for_admin(session: AsyncSession, order_id: int) -> dict | None:
    """Заказ с позициями и telegram_id пользователя для админки."""
    result = await session.execute(
        text("""
            SELECT o.id, o.status, o.full_name, o.address, o.phone, o.total, o.created_at,
                   u.telegram_id, u.username
            FROM orders_order o
            JOIN users_telegramuser u ON u.id = o.user_id
            WHERE o.id = :oid
        """),
        {"oid": order_id},
    )
    row = result.mappings().first()
    if not row:
        return None
    items_result = await session.execute(
        text("""
            SELECT oi.quantity, oi.price, p.name
            FROM orders_orderitem oi
            JOIN catalog_product p ON p.id = oi.product_id
            WHERE oi.order_id = :oid
        """),
        {"oid": order_id},
    )
    items = [dict(r) for r in items_result.mappings()]
    return {**dict(row), "items": items}


async def get_orders_list(
    session: AsyncSession,
    limit: int = 20,
    status_filter: str | None = None,
) -> list[dict]:
    """Список заказов для админа (последние limit)."""
    if status_filter:
        result = await session.execute(
            text("""
                SELECT o.id, o.status, o.full_name, o.total, o.created_at, u.telegram_id
                FROM orders_order o
                JOIN users_telegramuser u ON u.id = o.user_id
                WHERE o.status = :status
                ORDER BY o.created_at DESC
                LIMIT :limit
            """),
            {"limit": limit, "status": status_filter},
        )
    else:
        result = await session.execute(
            text("""
                SELECT o.id, o.status, o.full_name, o.total, o.created_at, u.telegram_id
                FROM orders_order o
                JOIN users_telegramuser u ON u.id = o.user_id
                ORDER BY o.created_at DESC
                LIMIT :limit
            """),
            {"limit": limit},
        )
    return [dict(row) for row in result.mappings()]
