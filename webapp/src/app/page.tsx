"use client";

import Link from "next/link";

export default function HomePage() {
  return (
    <div className="page">
      <header className="page__header">
        <div>
          <h1 className="page__title">Пчёлка</h1>
          <p className="page__subtitle">Магазин мёда и продуктов пасеки</p>
        </div>
      </header>

      <section className="mt-3">
        <Link href="/catalog" className="card card--clickable" style={{ display: "block", padding: 20 }}>
          <span style={{ fontSize: "2rem", display: "block", marginBottom: 8 }}>🍯</span>
          <strong style={{ fontSize: "1.125rem" }}>Каталог</strong>
          <p className="hint mt-1 mb-0" style={{ fontSize: "0.875rem" }}>
            Мёд, продукты пасеки, подарочные наборы
          </p>
        </Link>
      </section>

      <section className="mt-2">
        <Link href="/cart" className="card card--clickable" style={{ display: "block", padding: 20 }}>
          <span style={{ fontSize: "2rem", display: "block", marginBottom: 8 }}>🛒</span>
          <strong style={{ fontSize: "1.125rem" }}>Корзина</strong>
          <p className="hint mt-1 mb-0" style={{ fontSize: "0.875rem" }}>
            Просмотр и оформление заказа
          </p>
        </Link>
      </section>
    </div>
  );
}
