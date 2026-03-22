"use client";

import Link from "next/link";
import { HomeFaqSection } from "@/components/HomeFaqSection";

export default function HomePage() {
  return (
    <div className="page">
      <section className="card homeHero mt-2">
        <h1 className="homeHero__title">Пчёлка</h1>
        <p className="homeHero__subtitle">
          Натуральный мёд и продукты пасеки. Выбирайте любимые вкусы и оформляйте заказ в пару нажатий.
        </p>
      </section>

      <section className="mt-2 homeQuickGrid">
        <Link href="/catalog" className="card card--clickable homeCard">
          <span className="homeCard__iconWrap">
            <span className="homeCard__icon" aria-hidden>🍯</span>
          </span>
          <div className="homeCard__content">
            <strong className="homeCard__title">Каталог</strong>
            <p className="homeCard__desc">Мёд, наборы, продукты пасеки</p>
          </div>
        </Link>

        <Link href="/cart" className="card card--clickable homeCard">
          <span className="homeCard__iconWrap">
            <span className="homeCard__icon" aria-hidden>🛒</span>
          </span>
          <div className="homeCard__content">
            <strong className="homeCard__title">Корзина</strong>
            <p className="homeCard__desc">Проверить позиции и оформить</p>
          </div>
        </Link>
      </section>

      <HomeFaqSection />

      <section className="mt-2 card blockCard">
        <strong className="blockCard__title">Почему это удобно</strong>
        <p className="blockCard__text">
          Быстрая навигация сверху, понятные карточки товаров, оформление заказа прямо в Telegram.
        </p>
      </section>
    </div>
  );
}
