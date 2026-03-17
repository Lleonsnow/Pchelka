"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { setupBackButton, hideBackButton, setupMainButton, hideMainButton } from "@/lib/telegram";
import { getCart, createOrder } from "@/lib/api";

export default function CheckoutPage() {
  const router = useRouter();
  const [total, setTotal] = useState<string>("0");
  const [itemsCount, setItemsCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [form, setForm] = useState({ full_name: "", address: "", phone: "" });

  useEffect(() => {
    getCart()
      .then((data) => {
        setTotal(data.total);
        setItemsCount(data.items.length);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    setupBackButton(() => router.push("/cart"));
    return () => {
      hideBackButton();
      hideMainButton();
    };
  }, [router]);

  const handleSubmit = useCallback(() => {
    if (submitting || itemsCount === 0) return;
    const { full_name, address, phone } = form;
    if (!full_name.trim() || !address.trim() || !phone.trim()) {
      setError("Заполните ФИО, адрес и телефон");
      return;
    }
    setSubmitting(true);
    setError(null);
    createOrder({ full_name: full_name.trim(), address: address.trim(), phone: phone.trim() })
      .then(() => setSuccess(true))
      .catch((e) => {
        setError(e.message);
        setSubmitting(false);
      });
  }, [form, itemsCount, submitting]);

  useEffect(() => {
    if (success || loading || itemsCount === 0) {
      hideMainButton();
      return;
    }
    setupMainButton("Подтвердить заказ", handleSubmit);
    return () => hideMainButton();
  }, [success, loading, itemsCount, handleSubmit]);

  if (loading) {
    return (
      <div className="page">
        <div className="loading">Загрузка…</div>
      </div>
    );
  }

  if (itemsCount === 0 && !success) {
    return (
      <div className="page">
        <div className="empty-state card">
          <div className="empty-state__icon">🛒</div>
          <p className="mb-0">Корзина пуста</p>
          <Link href="/catalog" className="btn btn--primary mt-2">В каталог</Link>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="page">
        <div className="card" style={{ padding: 24, textAlign: "center" }}>
          <div style={{ fontSize: "3rem", marginBottom: 16 }}>✓</div>
          <h1 className="page__title mt-0 mb-1">Заказ оформлен</h1>
          <p className="text--secondary mb-0">
            Сумма: <strong className="text--price">{total} ₽</strong>. Мы свяжемся с вами для подтверждения и оплаты.
          </p>
          <Link href="/" className="btn btn--primary mt-3">На главную</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <header className="page__header">
        <div>
          <h1 className="page__title">Оформление заказа</h1>
          <p className="page__subtitle">Итого: {total} ₽</p>
        </div>
      </header>

      {error && <p className="error-msg">{error}</p>}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSubmit();
        }}
        className="card"
        style={{ padding: 20 }}
      >
        <label className="label">
          ФИО
          <input
            type="text"
            className="input"
            value={form.full_name}
            onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
            placeholder="Иван Иванов"
            required
          />
        </label>
        <label className="label" style={{ marginTop: 16 }}>
          Адрес доставки
          <input
            type="text"
            className="input"
            value={form.address}
            onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))}
            placeholder="Город, улица, дом, квартира"
            required
          />
        </label>
        <label className="label" style={{ marginTop: 16 }}>
          Телефон
          <input
            type="tel"
            className="input"
            value={form.phone}
            onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
            placeholder="+7 900 123-45-67"
            required
          />
        </label>
        <button
          type="submit"
          disabled={submitting}
          className="btn btn--primary"
          style={{ width: "100%", marginTop: 24 }}
        >
          {submitting ? "Отправка…" : "Подтвердить заказ"}
        </button>
      </form>

      <p className="mt-2">
        <Link href="/cart" className="text--secondary" style={{ fontSize: "0.875rem" }}>
          ← В корзину
        </Link>
      </p>
    </div>
  );
}
