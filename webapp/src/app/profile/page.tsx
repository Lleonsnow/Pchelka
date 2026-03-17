"use client";

import Link from "next/link";
import { useEffect } from "react";
import { hideBackButton, setupBackButton } from "@/lib/telegram";

export default function ProfilePage() {
  useEffect(() => {
    setupBackButton(() => window.history.back());
    return () => hideBackButton();
  }, []);

  return (
    <div className="page">
      <header className="page__header">
        <div>
          <h1 className="page__title">Профиль</h1>
          <p className="page__subtitle">Заказы и поддержка</p>
        </div>
      </header>

      <section className="card blockCard">
        <strong className="blockCard__title">Мои заказы</strong>
        <p className="blockCard__text">
          История заказов появится здесь, когда подключим API заказов для webapp.
        </p>
      </section>

      <section className="card blockCard mt-2">
        <strong className="blockCard__title">Поддержка</strong>
        <p className="blockCard__text">
          Вопросы по заказу или доставке — напишите в чат магазина в Telegram.
        </p>
      </section>

      <section className="card blockCard mt-2">
        <strong className="blockCard__title">Быстрые действия</strong>
        <div className="profileActions">
          <Link href="/catalog" className="btn btn--secondary btn--wide">
            Каталог
          </Link>
          <Link href="/cart" className="btn btn--primary btn--wide">
            Корзина
          </Link>
        </div>
      </section>
    </div>
  );
}

