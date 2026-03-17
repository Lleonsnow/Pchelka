"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { hideBackButton, setupBackButton } from "@/lib/telegram";
import { getCategories, getProducts, type Category, type Product } from "@/lib/api";

export default function CatalogPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const categoryId = searchParams.get("category");
  const productId = searchParams.get("product");
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const parentId = categoryId ? parseInt(categoryId, 10) : undefined;
  const isCategoryList = !categoryId && !productId;

  useEffect(() => {
    if (productId) {
      router.push(`/catalog/product/${productId}`);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    if (categoryId) {
      getProducts(parentId, search || undefined)
        .then((data) => {
          if (!cancelled) setProducts(data);
        })
        .catch((e) => {
          if (!cancelled) setError(e.message);
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    } else {
      getCategories()
        .then((data) => {
          if (!cancelled) setCategories(data);
        })
        .catch((e) => {
          if (!cancelled) setError(e.message);
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    }
    return () => {
      cancelled = true;
    };
  }, [categoryId, parentId, productId, router, search]);

  useEffect(() => {
    if (categoryId) {
      setupBackButton(() => router.push("/catalog"));
      return () => hideBackButton();
    }
    hideBackButton();
  }, [categoryId, router]);

  if (error) {
    return (
      <div className="page">
        <p className="error-msg">{error}</p>
        <Link href="/catalog" className="btn btn--secondary mt-2">← Каталог</Link>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="page">
        <div className="loading">Загрузка…</div>
      </div>
    );
  }

  return (
    <div className="page">
      <header className="page__header">
        <div>
          <h1 className="page__title">{categoryId ? "Товары" : "Каталог"}</h1>
          <p className="page__subtitle">
            {categoryId ? "Выберите товар" : "Мёд и продукты пасеки"}
          </p>
        </div>
      </header>

      {categoryId && (
        <div className="mt-2 mb-2">
          <input
            type="search"
            className="input"
            placeholder="Поиск по названию…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ marginTop: 0 }}
          />
        </div>
      )}

      {isCategoryList ? (
        <div className={`grid grid--categories mt-2`}>
          {categories.map((c) => (
            <Link
              key={c.id}
              href={`/catalog?category=${c.id}`}
              className="card card--clickable"
              style={{ padding: 20, textAlign: "center" }}
            >
              <span style={{ fontSize: "2rem", display: "block", marginBottom: 8 }}>🍯</span>
              <strong style={{ fontSize: "1rem", color: "var(--color-text)" }}>{c.name}</strong>
            </Link>
          ))}
        </div>
      ) : (
        <ul className="grid grid--products mt-2 list-divider">
          {products.map((p) => (
            <li key={p.id}>
              <Link
                href={`/catalog/product/${p.id}`}
                className="card card--clickable"
                style={{ display: "block", padding: 0 }}
              >
                {p.image_url ? (
                  <div style={{ aspectRatio: "1", overflow: "hidden", borderRadius: "var(--radius) var(--radius) 0 0" }}>
                    <img
                      src={p.image_url}
                      alt=""
                      style={{ width: "100%", height: "100%", objectFit: "cover" }}
                    />
                  </div>
                ) : (
                  <div style={{ aspectRatio: "1", background: "var(--color-cream-dark)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "2rem" }}>
                    🍯
                  </div>
                )}
                <div style={{ padding: 14 }}>
                  <strong style={{ fontSize: "0.9375rem", display: "block" }}>{p.name}</strong>
                  <span className="text--price" style={{ fontSize: "1rem", marginTop: 4, display: "block" }}>
                    {p.price} ₽
                  </span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
