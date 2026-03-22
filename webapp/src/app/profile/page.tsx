"use client";

import { useEffect } from "react";
import { hideBackButton, setupBackButton } from "@/lib/telegram";
import { useAsyncData } from "@/lib/useAsyncData";
import { getOrders, type OrderListItem } from "@/lib/api";

const STATUS_LABEL: Record<string, string> = {
  new: "Новый",
  confirmed: "Подтверждён",
  payment_pending: "Ожидает оплаты",
  paid: "Оплачен",
  shipped: "Отправлен",
  delivered: "Доставлен",
  cancelled: "Отменён",
};

function formatOrderDate(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("ru-RU", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  } catch {
    return iso.slice(0, 10);
  }
}

export default function ProfilePage() {
  const { data: orders, loading: ordersLoading } = useAsyncData<OrderListItem[]>(
    () => getOrders().catch(() => [] as OrderListItem[]),
    [],
  );

  useEffect(() => {
    setupBackButton(() => window.history.back());
    return () => hideBackButton();
  }, []);

  const list = orders ?? [];

  return (
    <div className="page page--profile">
      <header className="page__header">
        <h1 className="page__title">Профиль</h1>
        <p className="page__subtitle">Заказы и поддержка</p>
      </header>

      <section className="profileSection">
        <h2 className="profileSection__title">Мои заказы</h2>
        {ordersLoading ? (
          <p className="profileSection__muted">Загрузка…</p>
        ) : list.length === 0 ? (
          <p className="profileSection__muted">Пока нет заказов</p>
        ) : (
          <div className="orderListScroll">
            <ul className="orderList">
            {list.map((o) => (
              <li key={o.id} className="orderCard">
                <div className="orderCard__row">
                  <span className="orderCard__id">#{o.id}</span>
                  <span className="orderCard__date">{formatOrderDate(o.created_at)}</span>
                </div>
                <div className="orderCard__row orderCard__row--footer">
                  <span className="orderCard__status">{STATUS_LABEL[o.status] ?? o.status}</span>
                  <span className="orderCard__total">{o.total} ₽</span>
                </div>
              </li>
            ))}
            </ul>
          </div>
        )}
      </section>

      <section className="profileSection">
        <h2 className="profileSection__title">Поддержка</h2>
        <p className="profileSection__text">
          Вопросы по заказу или доставке — напишите в чат магазина в Telegram.
        </p>
      </section>
    </div>
  );
}
