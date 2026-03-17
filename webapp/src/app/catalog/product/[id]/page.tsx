"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
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
      <div className="page page--product">
        <p className="error-msg">{error}</p>
      </div>
    );
  }

  if (loading || !product) {
    return (
      <div className="page page--product">
        <div className="loading">Загрузка…</div>
      </div>
    );
  }

  return (
    <div className="page page--product">
      <article className="productCardDetail">
        <div className="productCardDetail__media">
          {product.image_urls?.length > 0 ? (
            <img src={product.image_urls[0]} alt={product.name} className="productCardDetail__img" />
          ) : (
            <span className="productCardDetail__placeholder" aria-hidden>🍯</span>
          )}
        </div>
        <div className="productCardDetail__body">
          <h1 className="productCardDetail__title">{product.name}</h1>
          <p className="productCardDetail__price">{product.price} ₽</p>
          {product.description && (
            <p className="productCardDetail__desc">{product.description}</p>
          )}
          <div className="productCardDetail__action">
            <button
              type="button"
              onClick={handleAddToCart}
              disabled={adding}
              className="btn btn--primary btn--full"
            >
              {adding ? "Добавляем…" : "В корзину"}
            </button>
          </div>
        </div>
      </article>
    </div>
  );
}
