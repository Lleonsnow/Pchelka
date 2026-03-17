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
      <div className="card mt-0" style={{ overflow: "hidden", marginBottom: 20 }}>
        {product.image_urls?.length > 0 ? (
          <div style={{ aspectRatio: "1", maxHeight: 320, background: "var(--color-cream-dark)" }}>
            <img
              src={product.image_urls[0]}
              alt={product.name}
              style={{ width: "100%", height: "100%", objectFit: "contain" }}
            />
          </div>
        ) : (
          <div style={{ aspectRatio: "1", maxHeight: 320, background: "var(--color-cream-dark)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "4rem" }}>
            🍯
          </div>
        )}
        <div style={{ padding: 20 }}>
          <h1 className="page__title mt-0 mb-1">{product.name}</h1>
          <p className="text--price" style={{ fontSize: "1.5rem", margin: "0 0 16px 0" }}>
            {product.price} ₽
          </p>
          {product.description && (
            <p className="text--secondary" style={{ whiteSpace: "pre-wrap", fontSize: "0.9375rem", lineHeight: 1.5 }}>
              {product.description}
            </p>
          )}
          <div className="flex gap-2 mt-3">
            <button
              type="button"
              onClick={handleAddToCart}
              disabled={adding}
              className="btn btn--primary"
            >
              {adding ? "Добавляем…" : "В корзину"}
            </button>
            <Link href="/cart" className="btn btn--secondary">
              Перейти в корзину
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
