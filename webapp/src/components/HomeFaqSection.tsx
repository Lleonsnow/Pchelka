"use client";

import { useEffect, useState } from "react";
import { getFaq, type FaqItem } from "@/lib/api";

export function HomeFaqSection() {
  const [items, setItems] = useState<FaqItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getFaq()
      .then((data) => {
        if (!cancelled) setItems(data);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Не удалось загрузить FAQ");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (items !== null && items.length === 0) {
    return null;
  }

  if (items === null && !error) {
    return (
      <section className="mt-2 card blockCard faqBlock" aria-busy="true">
        <p className="faqBlock__loading">Загрузка вопросов…</p>
      </section>
    );
  }

  if (error && items === null) {
    return (
      <section className="mt-2 card blockCard faqBlock faqBlock--error">
        <strong className="blockCard__title">Частые вопросы</strong>
        <p className="blockCard__text mt-1">{error}</p>
      </section>
    );
  }

  if (!items?.length) {
    return null;
  }

  return (
    <section className="mt-2 faqBlock" aria-labelledby="faq-heading">
      <div className="card blockCard faqBlock__intro">
        <h2 id="faq-heading" className="blockCard__title">
          Частые вопросы
        </h2>
        <p className="blockCard__text">Ответы о заказе, оплате и доставке.</p>
      </div>
      <ul className="faqBlock__list">
        {items.map((item) => (
          <li key={item.id}>
            <details className="faqItem">
              <summary className="faqItem__summary">{item.question}</summary>
              <div className="faqItem__answer">{item.answer}</div>
            </details>
          </li>
        ))}
      </ul>
    </section>
  );
}
