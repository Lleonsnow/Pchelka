"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { setupBackButton, hideBackButton } from "@/lib/telegram";
import {
  getCart,
  updateCartItem,
  removeFromCart,
  clearCart,
  type CartResponse,
} from "@/lib/api";

export default function CartPage() {
  const router = useRouter();
  const [data, setData] = useState<CartResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    getCart()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    setupBackButton(() => router.push("/"));
    return () => hideBackButton();
  }, [router]);

  const handleQuantity = (productId: number, delta: number) => {
    if (!data) return;
    const item = data.items.find((i) => i.product_id === productId);
    if (!item) return;
    const next = item.quantity + delta;
    if (next < 1) {
      removeFromCart(productId).then(setData).catch((e) => setError(e.message));
      return;
    }
    updateCartItem(productId, next).then(setData).catch((e) => setError(e.message));
  };

  const handleRemove = (productId: number) => {
    removeFromCart(productId).then(setData).catch((e) => setError(e.message));
  };

  const handleClear = () => {
    if (!confirm("Очистить корзину?")) return;
    clearCart()
      .then(() => setData({ items: [], total: "0" }))
      .catch((e) => setError(e.message));
  };

  if (error) {
    return (
      <div className="page">
        <p className="error-msg">{error}</p>
        <Link href="/" className="btn btn--secondary mt-2">← На главную</Link>
      </div>
    );
  }

  if (loading && !data) {
    return (
      <div className="page">
        <div className="loading">Загрузка…</div>
      </div>
    );
  }

  const items = data?.items ?? [];
  const total = data?.total ?? "0";

  return (
    <div className="page">
      <header className="page__header">
        <div>
          <h1 className="page__title">Корзина</h1>
          <p className="page__subtitle">
            {items.length === 0 ? "Пока пусто" : `${items.length} ${items.length === 1 ? "позиция" : "позиции"}`}
          </p>
        </div>
      </header>

      {items.length === 0 ? (
        <div className="empty-state card">
          <div className="empty-state__icon">🛒</div>
          <p className="mb-0">Корзина пуста</p>
          <Link href="/catalog" className="btn btn--primary mt-2">В каталог</Link>
        </div>
      ) : (
        <>
          <ul className="cartList">
            {items.map((item) => (
              <li key={item.id} className="card cartItem">
                <div className="cartItem__top">
                  <div>
                    <strong className="cartItem__name">{item.product_name}</strong>
                    <p className="hint cartItem__meta">
                      {item.price} ₽ × {item.quantity} = {item.subtotal} ₽
                    </p>
                  </div>
                  <div className="qtyControl" aria-label="Количество">
                    <button
                      type="button"
                      aria-label="Уменьшить"
                      onClick={() => handleQuantity(item.product_id, -1)}
                      className="btn btn--secondary btn--icon"
                    >
                      −
                    </button>
                    <span className="qtyControl__value">{item.quantity}</span>
                    <button
                      type="button"
                      aria-label="Увеличить"
                      onClick={() => handleQuantity(item.product_id, 1)}
                      className="btn btn--secondary btn--icon"
                    >
                      +
                    </button>
                    <button
                      type="button"
                      aria-label="Удалить"
                      onClick={() => handleRemove(item.product_id)}
                      className="btn btn--secondary btn--icon"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>

          <div className="cartSummarySticky">
            <div className="card cartSummary">
              <div className="cartSummary__row">
                <span className="text--secondary">Итого</span>
                <span className="text--price" style={{ fontSize: "1.25rem" }}>
                  {total} ₽
                </span>
              </div>
              <div className="cartSummary__actions">
                <button type="button" onClick={handleClear} className="btn btn--secondary btn--wide">
                  Очистить
                </button>
                <Link href="/checkout" className="btn btn--primary btn--wide">
                  Оформить
                </Link>
              </div>
            </div>
          </div>
        </>
      )}

      <p className="mt-3">
        <Link href="/catalog" className="text--secondary" style={{ fontSize: "0.875rem" }}>
          ← В каталог
        </Link>
      </p>
    </div>
  );
}
