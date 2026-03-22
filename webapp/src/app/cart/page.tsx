"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ShoppingCart, Trash2 } from "lucide-react";
import { setupBackButton, hideBackButton } from "@/lib/telegram";
import { useAsyncData } from "@/lib/useAsyncData";
import { getCart, updateCartItem, removeFromCart, clearCart } from "@/lib/api";

export default function CartPage() {
  const router = useRouter();
  const { data, setData, loading, error, setError, reload } = useAsyncData(
    () => getCart(),
    [],
  );

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
        <button type="button" onClick={() => reload()} className="btn btn--secondary mt-2">
          Повторить
        </button>
        <Link href="/" className="btn btn--secondary mt-2">На главную</Link>
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
    <div className="page page--cart">
      <header className="page__header">
        <h1 className="page__title">Корзина</h1>
        <p className="page__subtitle">
          {items.length === 0 ? "Пока пусто" : `${items.length} ${items.length === 1 ? "позиция" : "позиции"}`}
        </p>
      </header>

      {items.length === 0 ? (
        <div className="empty-state empty-state--cart">
          <span className="empty-state__icon" aria-hidden>
            <ShoppingCart strokeWidth={1.75} />
          </span>
          <p className="empty-state__text">Корзина пуста</p>
          <p className="empty-state__hint">Добавьте товары из каталога</p>
        </div>
      ) : (
        <>
          <ul className="cartList">
            {items.map((item) => (
              <li key={item.id} className="cartItem">
                <div className="cartItem__main">
                  <strong className="cartItem__name">{item.product_name}</strong>
                  <p className="cartItem__meta">
                    {item.price} ₽ × {item.quantity} = <strong>{item.subtotal} ₽</strong>
                  </p>
                </div>
                <div className="cartItem__actions">
                  <div className="qtyControl" aria-label="Количество">
                    <button
                      type="button"
                      aria-label="Уменьшить"
                      onClick={() => handleQuantity(item.product_id, -1)}
                      className="qtyControl__btn"
                    >
                      −
                    </button>
                    <span className="qtyControl__value">{item.quantity}</span>
                    <button
                      type="button"
                      aria-label="Увеличить"
                      onClick={() => handleQuantity(item.product_id, 1)}
                      className="qtyControl__btn"
                    >
                      +
                    </button>
                  </div>
                  <button
                    type="button"
                    aria-label="Удалить из корзины"
                    onClick={() => handleRemove(item.product_id)}
                    className="btn btn--danger btn--sm cartItem__removeBtn"
                  >
                    <Trash2 size={16} strokeWidth={2} aria-hidden />
                    Удалить
                  </button>
                </div>
              </li>
            ))}
          </ul>

          <div className="cartFooter">
            <div className="cartFooter__total">
              <span className="cartFooter__label">Итого</span>
              <span className="cartFooter__sum">{total} ₽</span>
            </div>
            <div className="cartFooter__btns">
              <button type="button" onClick={handleClear} className="btn btn--secondary">
                Очистить
              </button>
              <Link href="/checkout" className="btn btn--primary">
                Оформить заказ
              </Link>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
