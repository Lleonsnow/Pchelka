"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { setupBackButton, hideBackButton } from "@/lib/telegram";
import { getProduct, addToCart, type ProductDetail } from "@/lib/api";

export default function ProductPage() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getProduct(id)
      .then((data) => {
        if (!cancelled) setProduct(data);
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  useEffect(() => {
    setupBackButton(() => router.back());
    return () => hideBackButton();
  }, [router]);

  const handleAddToCart = () => {
    if (!product || adding) return;
    setAdding(true);
    addToCart(product.id, 1)
      .then(() => {
        setAdding(false);
      })
      .catch((e) => {
        setError(e.message);
        setAdding(false);
      });
  };

  if (error) {
    return (
      <div className="page">
        <p className="error-msg">{error}</p>
        <Link href="/catalog" className="btn btn--secondary mt-2">← Каталог</Link>
      </div>
    );
  }

  if (loading || !product) {
    return (
      <div className="page">
        <div className="loading">Загрузка…</div>
      </div>
    );
  }

  return (
    <div className="page">
      <section className="card productHero">
        <div className="productMedia">
          {product.image_urls?.length > 0 ? (
            <img src={product.image_urls[0]} alt={product.name} className="productMedia__img" />
          ) : (
            <span style={{ fontSize: "4rem" }} aria-hidden>
              🍯
            </span>
          )}
        </div>
        <div className="productBody">
          <h1 className="productTitle">{product.name}</h1>
          <p className="text--price productPrice">{product.price} ₽</p>
          {product.description && <p className="text--secondary productDesc">{product.description}</p>}

          <div className="productActions">
            <button type="button" onClick={handleAddToCart} disabled={adding} className="btn btn--primary btn--wide">
              {adding ? "Добавляем…" : "В корзину"}
            </button>
            <Link href="/cart" className="btn btn--secondary btn--wide">
              Перейти в корзину
            </Link>
          </div>
        </div>
      </section>

      <p className="mt-2">
        <Link href="/catalog" className="text--secondary" style={{ fontSize: "0.875rem" }}>
          ← Назад в каталог
        </Link>
      </p>
    </div>
  );
}
