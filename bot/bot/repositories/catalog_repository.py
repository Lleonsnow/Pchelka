from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

PER_PAGE = 6


@dataclass
class CategoryData:
    id: int
    parent_id: int | None
    name: str
    slug: str
    order: int

    @classmethod
    def from_row(cls, row: Any) -> "CategoryData":
        return cls(
            id=row["id"],
            parent_id=row["parent_id"],
            name=row["name"],
            slug=row["slug"],
            order=row["order"],
        )


@dataclass
class ProductData:
    id: int
    category_id: int
    name: str
    slug: str
    description: str
    price: Decimal
    image_paths: list[str]

    @classmethod
    def from_row(cls, row: Any, image_paths: list[str]) -> "ProductData":
        return cls(
            id=row["id"],
            category_id=row["category_id"],
            name=row["name"],
            slug=row["slug"],
            description=row["description"] or "",
            price=row["price"],
            image_paths=image_paths,
        )


async def get_root_categories(session: AsyncSession) -> list[CategoryData]:
    result = await session.execute(
        text("""
            SELECT id, parent_id, name, slug, "order"
            FROM catalog_category
            WHERE parent_id IS NULL
            ORDER BY "order", name
        """)
    )
    return [CategoryData.from_row(row) for row in result.mappings()]


async def get_child_categories(session: AsyncSession, parent_id: int) -> list[CategoryData]:
    result = await session.execute(
        text("""
            SELECT id, parent_id, name, slug, "order"
            FROM catalog_category
            WHERE parent_id = :pid
            ORDER BY "order", name
        """),
        {"pid": parent_id},
    )
    return [CategoryData.from_row(row) for row in result.mappings()]


async def get_category_by_id(session: AsyncSession, category_id: int) -> CategoryData | None:
    result = await session.execute(
        text("""
            SELECT id, parent_id, name, slug, "order"
            FROM catalog_category WHERE id = :id
        """),
        {"id": category_id},
    )
    row = result.mappings().first()
    return CategoryData.from_row(row) if row else None


async def get_products_count_in_category(session: AsyncSession, category_id: int) -> int:
    result = await session.execute(
        text("""
            SELECT COUNT(*) AS c FROM catalog_product
            WHERE category_id = :cid AND is_active = true
        """),
        {"cid": category_id},
    )
    row = result.mappings().first()
    return row["c"] if row else 0


async def get_products_in_category(
    session: AsyncSession,
    category_id: int,
    page: int = 0,
    per_page: int = PER_PAGE,
) -> list[ProductData]:
    offset = page * per_page
    result = await session.execute(
        text("""
            SELECT id, category_id, name, slug, description, price
            FROM catalog_product
            WHERE category_id = :cid AND is_active = true
            ORDER BY id
            LIMIT :limit OFFSET :offset
        """),
        {"cid": category_id, "limit": per_page, "offset": offset},
    )
    products = []
    for row in result.mappings():
        img_result = await session.execute(
            text("""
                SELECT image FROM catalog_productimage
                WHERE product_id = :pid ORDER BY "order", id
            """),
            {"pid": row["id"]},
        )
        paths = [
            (r["image"] or "").strip()
            for r in img_result.mappings()
            if (r.get("image") or "").strip()
        ]
        products.append(ProductData.from_row(row, paths))
    return products


async def get_product_by_id(session: AsyncSession, product_id: int) -> ProductData | None:
    result = await session.execute(
        text("""
            SELECT id, category_id, name, slug, description, price
            FROM catalog_product WHERE id = :id AND is_active = true
        """),
        {"id": product_id},
    )
    row = result.mappings().first()
    if not row:
        return None
    img_result = await session.execute(
        text("""
            SELECT image FROM catalog_productimage
            WHERE product_id = :pid ORDER BY "order", id
        """),
        {"pid": row["id"]},
    )
    paths = [
        (r["image"] or "").strip()
        for r in img_result.mappings()
        if (r.get("image") or "").strip()
    ]
    return ProductData.from_row(row, paths)


async def get_children_count(session: AsyncSession, category_id: int) -> int:
    result = await session.execute(
        text("SELECT COUNT(*) AS c FROM catalog_category WHERE parent_id = :pid"),
        {"pid": category_id},
    )
    row = result.mappings().first()
    return row["c"] if row else 0
