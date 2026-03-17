from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class CartItemData:
    id: int
    product_id: int
    product_name: str
    price: Decimal
    quantity: int

    @property
    def subtotal(self) -> Decimal:
        return self.price * self.quantity

    @classmethod
    def from_row(cls, row: Any) -> "CartItemData":
        return cls(
            id=row["id"],
            product_id=row["product_id"],
            product_name=row["product_name"],
            price=row["price"],
            quantity=row["quantity"],
        )


async def get_or_create_cart(session: AsyncSession, user_id: int) -> int:
    """Возвращает cart_id для user_id. Создаёт корзину при необходимости."""
    result = await session.execute(
        text("SELECT id FROM cart_cart WHERE user_id = :uid"),
        {"uid": user_id},
    )
    row = result.mappings().first()
    if row:
        return row["id"]
    await session.execute(
        text("INSERT INTO cart_cart (user_id, updated_at) VALUES (:uid, NOW())"),
        {"uid": user_id},
    )
    result = await session.execute(
        text("SELECT id FROM cart_cart WHERE user_id = :uid"),
        {"uid": user_id},
    )
    return result.mappings().first()["id"]


async def get_cart_items(session: AsyncSession, user_id: int) -> list[CartItemData]:
    """Список позиций корзины с названием и ценой товара."""
    cart_id = await get_or_create_cart(session, user_id)
    result = await session.execute(
        text("""
            SELECT ci.id, ci.product_id, ci.quantity, p.name AS product_name, p.price
            FROM cart_cartitem ci
            JOIN catalog_product p ON p.id = ci.product_id
            WHERE ci.cart_id = :cid
            ORDER BY ci.id
        """),
        {"cid": cart_id},
    )
    return [CartItemData.from_row(row) for row in result.mappings()]


async def get_cart_total(session: AsyncSession, user_id: int) -> Decimal:
    """Итоговая сумма корзины."""
    items = await get_cart_items(session, user_id)
    return sum(i.subtotal for i in items)


async def add_to_cart(
    session: AsyncSession,
    user_id: int,
    product_id: int,
    quantity: int = 1,
) -> None:
    """Добавить товар в корзину или увеличить количество."""
    cart_id = await get_or_create_cart(session, user_id)
    result = await session.execute(
        text("""
            SELECT id, quantity FROM cart_cartitem
            WHERE cart_id = :cid AND product_id = :pid
        """),
        {"cid": cart_id, "pid": product_id},
    )
    row = result.mappings().first()
    if row:
        await session.execute(
            text("""
                UPDATE cart_cartitem SET quantity = quantity + :q
                WHERE cart_id = :cid AND product_id = :pid
            """),
            {"cid": cart_id, "pid": product_id, "q": quantity},
        )
    else:
        await session.execute(
            text("""
                INSERT INTO cart_cartitem (cart_id, product_id, quantity)
                VALUES (:cid, :pid, :q)
            """),
            {"cid": cart_id, "pid": product_id, "q": quantity},
        )


async def update_cart_item_quantity(
    session: AsyncSession,
    user_id: int,
    cart_item_id: int,
    delta: int,
) -> bool:
    """Изменить количество позиции на delta. Удаляет позицию, если quantity <= 0. Возвращает True если позиция ещё есть."""
    cart_id = await get_or_create_cart(session, user_id)
    result = await session.execute(
        text("""
            SELECT quantity FROM cart_cartitem
            WHERE id = :id AND cart_id = :cid
        """),
        {"id": cart_item_id, "cid": cart_id},
    )
    row = result.mappings().first()
    if not row:
        return False
    new_q = row["quantity"] + delta
    if new_q <= 0:
        await session.execute(
            text("DELETE FROM cart_cartitem WHERE id = :id AND cart_id = :cid"),
            {"id": cart_item_id, "cid": cart_id},
        )
        return False
    await session.execute(
        text("UPDATE cart_cartitem SET quantity = :q WHERE id = :id AND cart_id = :cid"),
        {"q": new_q, "id": cart_item_id, "cid": cart_id},
    )
    return True


async def remove_cart_item(
    session: AsyncSession,
    user_id: int,
    cart_item_id: int,
) -> bool:
    """Удалить позицию из корзины."""
    cart_id = await get_or_create_cart(session, user_id)
    result = await session.execute(
        text("DELETE FROM cart_cartitem WHERE id = :id AND cart_id = :cid"),
        {"id": cart_item_id, "cid": cart_id},
    )
    return result.rowcount > 0


async def clear_cart(session: AsyncSession, user_id: int) -> None:
    """Очистить корзину."""
    result = await session.execute(
        text("SELECT id FROM cart_cart WHERE user_id = :uid"),
        {"uid": user_id},
    )
    row = result.mappings().first()
    if row:
        await session.execute(
            text("DELETE FROM cart_cartitem WHERE cart_id = :cid"),
            {"cid": row["id"]},
        )
