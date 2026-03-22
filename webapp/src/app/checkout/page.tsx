"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  setupBackButton,
  hideBackButton,
  setupMainButton,
  hideMainButton,
  getTelegramWebApp,
} from "@/lib/telegram";
import { getCart, createOrder } from "@/lib/api";

const CHECKOUT_STORAGE_KEY = "tg-shop-checkout-last";

function getSavedCheckoutData(): { full_name: string; address: string; phone: string } {
  if (typeof window === "undefined") return { full_name: "", address: "", phone: "" };
  try {
    const raw = localStorage.getItem(CHECKOUT_STORAGE_KEY);
    if (!raw) return { full_name: "", address: "", phone: "" };
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    return {
      full_name: typeof parsed.full_name === "string" ? parsed.full_name : "",
      address: typeof parsed.address === "string" ? parsed.address : "",
      phone: typeof parsed.phone === "string" ? parsed.phone : "",
    };
  } catch {
    return { full_name: "", address: "", phone: "" };
  }
}

function saveCheckoutData(data: { full_name: string; address: string; phone: string }) {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(CHECKOUT_STORAGE_KEY, JSON.stringify(data));
  } catch {
    // ignore
  }
}

export default function CheckoutPage() {
  const router = useRouter();
  const submitRef = useRef<() => void>(() => {});
  const [hasTelegramMainButton, setHasTelegramMainButton] = useState(false);
  const [total, setTotal] = useState<string>("0");
  const [itemsCount, setItemsCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [form, setForm] = useState({ full_name: "", address: "", phone: "" });
  const [fieldErrors, setFieldErrors] = useState<{ full_name?: string; address?: string; phone?: string }>({});

  useEffect(() => {
    setForm((prev) => {
      const saved = getSavedCheckoutData();
      if (!saved.full_name && !saved.address && !saved.phone) return prev;
      return saved;
    });
  }, []);

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
    return () => hideBackButton();
  }, [router]);

  const handleSubmit = useCallback(() => {
    if (submitting || itemsCount === 0) return;
    const { full_name, address, phone } = form;

    const nextErrors: { full_name?: string; address?: string; phone?: string } = {};

    const nameTrimmed = full_name.trim();
    if (!nameTrimmed) {
      nextErrors.full_name = "Введите ФИО";
    } else if (nameTrimmed.length < 5 || !nameTrimmed.includes(" ")) {
      nextErrors.full_name = "Укажите имя и фамилию полностью";
    }

    const addressTrimmed = address.trim();
    if (!addressTrimmed) {
      nextErrors.address = "Введите адрес доставки";
    } else if (addressTrimmed.length < 10) {
      nextErrors.address = "Адрес слишком короткий";
    }

    const phoneTrimmed = phone.trim();
    const phoneNormalized = phoneTrimmed.replace(/[^+0-9]/g, "");
    const phoneOk = /^(\+7|7|8)[0-9]{10}$/.test(phoneNormalized);
    if (!phoneTrimmed) {
      nextErrors.phone = "Введите телефон";
    } else if (!phoneOk) {
      nextErrors.phone = "Формат телефона: +7 900 123-45-67";
    }

    if (nextErrors.full_name || nextErrors.address || nextErrors.phone) {
      setFieldErrors(nextErrors);
      setError(null);
      return;
    }

    setFieldErrors({});
    setSubmitting(true);
    setError(null);
    const payload = { full_name: nameTrimmed, address: addressTrimmed, phone: phoneTrimmed };
    createOrder(payload)
      .then(() => {
        saveCheckoutData(payload);
        setSuccess(true);
      })
      .catch((e) => {
        setError(e.message);
        setSubmitting(false);
      });
  }, [form, itemsCount, submitting]);

  useEffect(() => {
    submitRef.current = handleSubmit;
  }, [handleSubmit]);

  useEffect(() => {
    setupMainButton("Подтвердить заказ", () => submitRef.current());
    setHasTelegramMainButton(!!getTelegramWebApp()?.MainButton);
    return () => hideMainButton();
  }, []);

  useEffect(() => {
    const mainButton = getTelegramWebApp()?.MainButton;
    if (!mainButton) return;
    if (loading || success || itemsCount === 0) {
      mainButton.hide();
      return;
    }
    mainButton.setText(submitting ? "Отправка..." : "Подтвердить заказ");
    mainButton.show();
  }, [loading, success, itemsCount, submitting]);


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
        <div className="empty-state empty-state--cart">
          <span className="empty-state__icon" aria-hidden>🛒</span>
          <p className="empty-state__text">Корзина пуста</p>
          <p className="empty-state__hint">Добавьте товары из каталога</p>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="page">
        <div className="card successCard">
          <div className="successMark" aria-hidden>✓</div>
          <h1 className="page__title mt-0 mb-1">Заказ оформлен</h1>
          <p className="text--secondary mb-0">
            Сумма: <strong className="text--price">{total} ₽</strong>. Мы свяжемся с вами для подтверждения и оплаты.
          </p>
          <Link href="/" className="btn btn--primary btn--full mt-3">На главную</Link>
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
        className="card checkoutCard"
      >
        <div className="formGrid">
          <label className="label">
            ФИО
            <input
              type="text"
              className={"input" + (fieldErrors.full_name ? " input--error" : "")}
              aria-invalid={!!fieldErrors.full_name}
              aria-describedby={fieldErrors.full_name ? "checkout-fullname-error" : undefined}
              value={form.full_name}
              onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
              placeholder="Иван Иванов"
              required
              autoComplete="name"
            />
            {fieldErrors.full_name && (
              <p className="fieldError" id="checkout-fullname-error">
                {fieldErrors.full_name}
              </p>
            )}
          </label>
          <label className="label">
            Адрес доставки
            <input
              type="text"
              className={"input" + (fieldErrors.address ? " input--error" : "")}
              aria-invalid={!!fieldErrors.address}
              aria-describedby={fieldErrors.address ? "checkout-address-error" : undefined}
              value={form.address}
              onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))}
              placeholder="Город, улица, дом, квартира"
              required
              autoComplete="street-address"
            />
            {fieldErrors.address && (
              <p className="fieldError" id="checkout-address-error">
                {fieldErrors.address}
              </p>
            )}
          </label>
          <label className="label">
            Телефон
            <input
              type="tel"
              className={"input" + (fieldErrors.phone ? " input--error" : "")}
              aria-invalid={!!fieldErrors.phone}
              aria-describedby={fieldErrors.phone ? "checkout-phone-error" : undefined}
              value={form.phone}
              onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
              placeholder="+7 900 123-45-67"
              required
              inputMode="tel"
              autoComplete="tel"
            />
            {fieldErrors.phone && (
              <p className="fieldError" id="checkout-phone-error">
                {fieldErrors.phone}
              </p>
            )}
          </label>
        </div>
        <div className="inputHintRow">
          <span>Проверим данные и свяжемся для подтверждения.</span>
          <span>Итого: {total} ₽</span>
        </div>
        {!hasTelegramMainButton && (
          <button
            type="submit"
            disabled={submitting}
            className="btn btn--primary btn--full"
            style={{ marginTop: 18 }}
          >
            {submitting ? "Отправка…" : "Подтвердить заказ"}
          </button>
        )}
      </form>
    </div>
  );
}
